"""Fixture generation service — round-robin + EFL playoff bracket."""
from ..models.match import Match


def generate_round_robin(tournament, players):
    """Generate all round-robin league fixtures using the circle method.
    
    Returns a flat list of Match objects (not yet added to session).
    """
    player_ids = [p.id for p in players]
    n = len(player_ids)
    if n < 2:
        raise ValueError("Need at least 2 players to generate fixtures.")

    # Pad to even number with a BYE (None)
    if n % 2 == 1:
        player_ids.append(None)
        n += 1

    half = n // 2
    matches = []
    match_order = 1

    for round_num in range(n - 1):
        round_name = f"Matchday {round_num + 1}"
        for i in range(half):
            p1 = player_ids[i]
            p2 = player_ids[n - 1 - i]
            if p1 is None or p2 is None:
                continue  # Skip BYE matches
            match = Match(
                tournament_id=tournament.id,
                round_name=round_name,
                stage='league',
                match_order=match_order,
                player1_id=p1,
                player2_id=p2,
                status='scheduled',
            )
            matches.append(match)
            match_order += 1

        # Rotate: keep first fixed, rotate the rest
        player_ids = [player_ids[0]] + [player_ids[-1]] + player_ids[1:-1]

    return matches


def generate_playoff_bracket(tournament, standings, db_session):
    """Generate EFL playoff bracket from top-6 standings.
    
    Bracket:
      QF1: 3rd vs 6th
      QF2: 4th vs 5th
      SF1: 2nd vs winner(QF1)
      SF2: 1st vs winner(QF2)
      Final: winner(SF1) vs winner(SF2)
    
    Returns list of Match objects added to db_session (not yet committed).
    """
    if len(standings) < 6:
        raise ValueError("Need at least 6 players to generate playoffs.")

    top6 = standings[:6]  # [1st, 2nd, 3rd, 4th, 5th, 6th]

    # Create Final first (so we can set next_match_id on earlier rounds)
    final = Match(
        tournament_id=tournament.id,
        round_name='Final',
        stage='playoff',
        match_order=5,
        player1_id=None,
        player2_id=None,
        status='scheduled',
    )
    db_session.add(final)
    db_session.flush()

    # Semi-Finals
    sf1 = Match(
        tournament_id=tournament.id,
        round_name='Semi-Final 1',
        stage='playoff',
        match_order=3,
        player1_id=top6[1]['player_id'],  # 2nd place
        player2_id=None,  # winner of QF1
        status='scheduled',
        next_match_id=final.id,
        next_match_slot=1,
    )
    sf2 = Match(
        tournament_id=tournament.id,
        round_name='Semi-Final 2',
        stage='playoff',
        match_order=4,
        player1_id=top6[0]['player_id'],  # 1st place
        player2_id=None,  # winner of QF2
        status='scheduled',
        next_match_id=final.id,
        next_match_slot=2,
    )
    db_session.add(sf1)
    db_session.add(sf2)
    db_session.flush()

    # Quarter-Finals
    qf1 = Match(
        tournament_id=tournament.id,
        round_name='Quarter-Final 1',
        stage='playoff',
        match_order=1,
        player1_id=top6[2]['player_id'],  # 3rd place
        player2_id=top6[5]['player_id'],  # 6th place
        status='scheduled',
        next_match_id=sf1.id,
        next_match_slot=2,  # winner fills slot 2 of SF1
    )
    qf2 = Match(
        tournament_id=tournament.id,
        round_name='Quarter-Final 2',
        stage='playoff',
        match_order=2,
        player1_id=top6[3]['player_id'],  # 4th place
        player2_id=top6[4]['player_id'],  # 5th place
        status='scheduled',
        next_match_id=sf2.id,
        next_match_slot=2,  # winner fills slot 2 of SF2
    )
    db_session.add(qf1)
    db_session.add(qf2)
    db_session.flush()

    return [qf1, qf2, sf1, sf2, final]


def advance_playoff_winner(match, db_session):
    """After a playoff match is completed, advance the winner to the next match."""
    if not match.next_match_id:
        return  # This is the Final — no advancement needed

    winner_id = match.winner_player_id()
    if winner_id is None:
        return

    next_match = db_session.get(Match, match.next_match_id)
    if next_match is None:
        return

    if match.next_match_slot == 1:
        next_match.player1_id = winner_id
    else:
        next_match.player2_id = winner_id
