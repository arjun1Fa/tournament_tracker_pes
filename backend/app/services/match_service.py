"""Match service — report and verify match results.

Handles the two-stage identification flow:
    1. Reporter submits OCR data + selects "which team are you?"
    2. Opponent verifies + selects their team
    3. Both confirmed → match verified, stats permanently assigned
"""
from ..extensions import db
from ..models.match import Match
from ..models.match_stats import MatchStats
from ..models.user import User


STAT_FIELDS = [
    'possession', 'shots', 'shots_on_target', 'fouls', 'offsides',
    'corner_kicks', 'free_kicks', 'passes', 'successful_passes',
    'crosses', 'interceptions', 'tackles', 'saves',
]


def report_match(match_id, reporter_id, data):
    """Submit a match result with OCR-extracted stats.

    Args:
        match_id: ID of the match being reported.
        reporter_id: User ID of the reporter.
        data: Dict containing:
            - team1_name: str (e.g., "joshua")
            - team2_name: str (e.g., "La Remontada")
            - score1: int
            - score2: int
            - my_team: "team1" or "team2" (which side the reporter played)
            - team1_stats: dict of stat fields for team1
            - team2_stats: dict of stat fields for team2

    Returns:
        Tuple of (match_dict, error_message, status_code).
    """
    match = db.session.get(Match, match_id)
    if not match:
        return None, 'Match not found.', 404

    if match.status != 'scheduled':
        return None, f'Match cannot be reported (status: {match.status}).', 400

    # Verify reporter is a participant in this match
    if reporter_id not in (match.player1_id, match.player2_id):
        return None, 'You are not a participant in this match.', 403

    # Extract data
    team1_name = data.get('team1_name', '').strip()
    team2_name = data.get('team2_name', '').strip()
    score1 = data.get('score1')
    score2 = data.get('score2')
    my_team = data.get('my_team')

    if not team1_name or not team2_name:
        return None, 'Both team names are required.', 400
    if score1 is None or score2 is None:
        return None, 'Both scores are required.', 400
    if my_team not in ('team1', 'team2'):
        return None, 'my_team must be "team1" or "team2".', 400

    try:
        score1 = int(score1)
        score2 = int(score2)
    except (ValueError, TypeError):
        return None, 'Scores must be integers.', 400

    # Update match
    match.team1_name = team1_name
    match.team2_name = team2_name
    match.score1 = score1
    match.score2 = score2
    match.reported_by = reporter_id
    match.status = 'pending_verification'

    # Determine which player maps to which team
    if my_team == 'team1':
        reporter_team_name = team1_name
        reporter_stats_data = data.get('team1_stats', {})
        opponent_team_name = team2_name
        opponent_stats_data = data.get('team2_stats', {})
        # Reporter claims to be team1
        if reporter_id == match.player1_id:
            match.verified_by_player1 = True
        else:
            match.verified_by_player2 = True
    else:
        reporter_team_name = team2_name
        reporter_stats_data = data.get('team2_stats', {})
        opponent_team_name = team1_name
        opponent_stats_data = data.get('team1_stats', {})
        if reporter_id == match.player1_id:
            match.verified_by_player1 = True
        else:
            match.verified_by_player2 = True

    # Determine opponent user ID
    opponent_id = match.player2_id if reporter_id == match.player1_id else match.player1_id

    # Create MatchStats for reporter
    reporter_stat = MatchStats(
        match_id=match_id,
        user_id=reporter_id,
        team_name=reporter_team_name,
    )
    _fill_stats(reporter_stat, reporter_stats_data)
    db.session.add(reporter_stat)

    # Create MatchStats for opponent (preliminary — may be reassigned on verify)
    opponent_stat = MatchStats(
        match_id=match_id,
        user_id=opponent_id,
        team_name=opponent_team_name,
    )
    _fill_stats(opponent_stat, opponent_stats_data)
    db.session.add(opponent_stat)

    db.session.commit()

    return match.to_dict(include_stats=True), None, 200


def verify_match(match_id, verifier_id, data):
    """Opponent verifies (or disputes) a reported match.

    Args:
        match_id: ID of the match.
        verifier_id: User ID of the verifying opponent.
        data: Dict containing:
            - my_team: "team1" or "team2" (which side the verifier played)
            - confirmed: bool (True = accept, False = dispute)

    Returns:
        Tuple of (match_dict, error_message, status_code).
    """
    match = db.session.get(Match, match_id)
    if not match:
        return None, 'Match not found.', 404

    if match.status != 'pending_verification':
        return None, f'Match is not pending verification (status: {match.status}).', 400

    # Verify this user is the opponent (not the reporter)
    if verifier_id not in (match.player1_id, match.player2_id):
        return None, 'You are not a participant in this match.', 403

    if verifier_id == match.reported_by:
        return None, 'You already reported this match. Wait for your opponent to verify.', 400

    confirmed = data.get('confirmed', False)
    my_team = data.get('my_team')

    if not confirmed:
        # Dispute
        match.status = 'disputed'
        db.session.commit()
        return match.to_dict(), None, 200

    if my_team not in ('team1', 'team2'):
        return None, 'my_team must be "team1" or "team2".', 400

    # Mark verification
    if verifier_id == match.player1_id:
        match.verified_by_player1 = True
    else:
        match.verified_by_player2 = True

    # Both verified → match is verified
    if match.verified_by_player1 and match.verified_by_player2:
        match.status = 'verified'

    db.session.commit()

    return match.to_dict(include_stats=True), None, 200


def advance_winner(match):
    """After a knockout match is verified, advance the winner.

    Checks if the next match in the bracket exists and fills in the winner.
    """
    if match.score1 is None or match.score2 is None:
        return

    # Determine winner
    if match.score1 > match.score2:
        winner_id = match.player1_id
    elif match.score2 > match.score1:
        winner_id = match.player2_id
    else:
        # Draw in knockout shouldn't happen (extra time/penalties)
        # But if it does, don't advance anyone
        return

    # Find the next round match based on bracket structure
    round_name = match.round
    match_order = match.match_order

    next_round = _get_next_round(round_name)
    if not next_round:
        return  # This was the Grand Final

    # Determine which slot in the next round
    # Matches feed into the next round in pairs: match 1&2 → next match 1, etc.
    next_match_order = (match_order + 1) // 2

    # Special handling for EFL knockout seeding
    if round_name == 'Qualification Round':
        # Q1 winner (match_order=1, 3rd vs 5th) → SF2 (player2 of SF match_order=2)
        # Q2 winner (match_order=2, 4th vs 6th) → SF1 (player2 of SF match_order=1)
        if match_order == 1:
            next_match = Match.query.filter_by(
                tournament_id=match.tournament_id,
                round='Semi-Final',
                match_order=2,
            ).first()
        else:
            next_match = Match.query.filter_by(
                tournament_id=match.tournament_id,
                round='Semi-Final',
                match_order=1,
            ).first()

        if next_match:
            next_match.player2_id = winner_id
            db.session.commit()
        return

    if round_name == 'Semi-Final':
        next_match = Match.query.filter_by(
            tournament_id=match.tournament_id,
            round='Grand Final',
            match_order=1,
        ).first()

        if next_match:
            if match_order == 1:
                next_match.player1_id = winner_id
            else:
                next_match.player2_id = winner_id
            db.session.commit()
        return

    # Generic bracket advancement for single_elim
    next_match = Match.query.filter_by(
        tournament_id=match.tournament_id,
        round=next_round,
        match_order=next_match_order,
    ).first()

    if next_match:
        if match_order % 2 == 1:
            next_match.player1_id = winner_id
        else:
            next_match.player2_id = winner_id
        db.session.commit()


def _fill_stats(stat_obj, stats_data):
    """Fill a MatchStats object from a dict of stat values."""
    for field in STAT_FIELDS:
        value = stats_data.get(field)
        if value is not None:
            try:
                if field == 'possession':
                    setattr(stat_obj, field, float(value))
                else:
                    setattr(stat_obj, field, int(value))
            except (ValueError, TypeError):
                pass  # Skip invalid values


def _get_next_round(current_round):
    """Map current round to the next round in knockout brackets."""
    progression = {
        'Qualification Round': 'Semi-Final',
        'Semi-Final': 'Grand Final',
        'Quarter-Final': 'Semi-Final',
        'Round 1': 'Quarter-Final',
    }
    return progression.get(current_round)
