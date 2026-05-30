"""Tournament fixture generation service.

Supports the EFL format (double round-robin league + 6-team knockout)
and a generic round-robin format. New formats are added as functions.
"""
from itertools import combinations

from ..models.match import Match


def generate_fixtures(tournament, participants):
    """Generate all fixtures for a tournament based on its format.

    Args:
        tournament: Tournament model instance.
        participants: List of TournamentParticipant instances, ordered by seed.

    Returns:
        List of Match model instances (not yet committed).

    Raises:
        ValueError: If format is unsupported or participant count is invalid.
    """
    format_type = tournament.format
    generators = {
        'efl': _generate_efl_fixtures,
        'round_robin': _generate_round_robin_fixtures,
        'single_elim': _generate_single_elim_fixtures,
    }

    generator = generators.get(format_type)
    if not generator:
        raise ValueError(f'Unsupported tournament format: {format_type}')

    return generator(tournament, participants)


# ---------------------------------------------------------------------------
# EFL Format: Double Round-Robin (League Phase) + 6-Team Knockout
# Per rulebook: 10 clubs, 18 matches each (home & away), top 6 to knockout
# ---------------------------------------------------------------------------

def _generate_efl_fixtures(tournament, participants):
    """Generate EFL Season fixtures.

    Stage I — League Phase:
        Double round-robin (every pair plays twice: home & away).
        Uses the circle method to schedule balanced rounds.

    Stage II — Knockout Phase:
        NOT generated upfront. Knockout matches are created after
        the league phase completes, based on final standings.
        (See create_knockout_fixtures() for that.)

    With N participants:
        - Rounds: 2 * (N-1)
        - Matches per round: N // 2
        - Total matches: N * (N-1)
    """
    n = len(participants)
    if n < 2:
        raise ValueError('EFL format requires at least 2 participants.')

    player_ids = [p.user_id for p in participants]
    matches = []

    # Use circle method for round-robin scheduling
    # This ensures each player plays once per round with balanced home/away
    first_leg_rounds = _circle_method_schedule(player_ids)

    match_order = 0

    # First leg (Rounds 1 to N-1): as scheduled
    for round_num, round_pairs in enumerate(first_leg_rounds, start=1):
        for home_id, away_id in round_pairs:
            match_order += 1
            matches.append(Match(
                tournament_id=tournament.id,
                round=f'Matchday {round_num}',
                match_order=match_order,
                player1_id=home_id,
                player2_id=away_id,
                status='scheduled',
            ))

    # Second leg (Rounds N to 2N-2): swap home/away
    for round_num, round_pairs in enumerate(first_leg_rounds, start=n):
        for home_id, away_id in round_pairs:
            match_order += 1
            matches.append(Match(
                tournament_id=tournament.id,
                round=f'Matchday {round_num}',
                match_order=match_order,
                player1_id=away_id,   # Swapped
                player2_id=home_id,   # Swapped
                status='scheduled',
            ))

    return matches


def _circle_method_schedule(player_ids):
    """Generate a round-robin schedule using the circle (polygon) method.

    For N players (N must be even; if odd, a BYE is added):
    - Fix player[0] in position 0.
    - Rotate the remaining players each round.
    - Each round produces N/2 pairings.

    Returns:
        List of rounds, where each round is a list of (home_id, away_id) tuples.
    """
    players = list(player_ids)
    n = len(players)

    # If odd number, add a "BYE" placeholder (None)
    if n % 2 == 1:
        players.append(None)
        n += 1

    rounds = []
    # Fix first player, rotate the rest
    fixed = players[0]
    rotating = players[1:]

    for round_idx in range(n - 1):
        round_players = [fixed] + rotating
        round_pairs = []

        for i in range(n // 2):
            home = round_players[i]
            away = round_players[n - 1 - i]

            # Skip BYE matches
            if home is None or away is None:
                continue

            round_pairs.append((home, away))

        rounds.append(round_pairs)

        # Rotate: move last element to the front of rotating list
        rotating = [rotating[-1]] + rotating[:-1]

    return rounds


def create_knockout_fixtures(tournament, standings):
    """Create knockout phase fixtures from league standings.

    Per EFL rulebook Article 05:
        Qualification Round:
            Q1: 3rd vs 5th
            Q2: 4th vs 6th

        Semi-Finals:
            SF1: 1st vs Winner of Q2 (4th vs 6th)
            SF2: 2nd vs Winner of Q1 (3rd vs 5th)

        Grand Final:
            Winner of SF1 vs Winner of SF2

    Args:
        tournament: Tournament model instance.
        standings: List of dicts with 'user_id' key, ordered by rank (1st first).

    Returns:
        List of Match instances for the knockout phase.
        Q1 and Q2 are fully populated. SF and Final have placeholders.
    """
    if len(standings) < 6:
        raise ValueError('Need at least 6 players in standings for knockout phase.')

    # Top 6 by rank
    first = standings[0]['user_id']
    second = standings[1]['user_id']
    third = standings[2]['user_id']
    fourth = standings[3]['user_id']
    fifth = standings[4]['user_id']
    sixth = standings[5]['user_id']

    matches = []

    # Qualification Round
    # Q1: 3rd vs 5th
    matches.append(Match(
        tournament_id=tournament.id,
        round='Qualification Round',
        match_order=1,
        player1_id=third,
        player2_id=fifth,
        status='scheduled',
    ))

    # Q2: 4th vs 6th
    matches.append(Match(
        tournament_id=tournament.id,
        round='Qualification Round',
        match_order=2,
        player1_id=fourth,
        player2_id=sixth,
        status='scheduled',
    ))

    # Semi-Finals (players TBD — will be filled after qualification)
    # SF1: 1st vs Winner of Q2
    matches.append(Match(
        tournament_id=tournament.id,
        round='Semi-Final',
        match_order=1,
        player1_id=first,
        player2_id=None,  # Winner of Q2, filled later
        status='scheduled',
    ))

    # SF2: 2nd vs Winner of Q1
    matches.append(Match(
        tournament_id=tournament.id,
        round='Semi-Final',
        match_order=2,
        player1_id=second,
        player2_id=None,  # Winner of Q1, filled later
        status='scheduled',
    ))

    # Grand Final (both players TBD)
    matches.append(Match(
        tournament_id=tournament.id,
        round='Grand Final',
        match_order=1,
        player1_id=None,  # Filled after SF1 — but FK requires a value
        player2_id=None,  # Filled after SF2
        status='scheduled',
    ))

    return matches


# ---------------------------------------------------------------------------
# Generic Round-Robin (single round-robin, no knockout)
# ---------------------------------------------------------------------------

def _generate_round_robin_fixtures(tournament, participants):
    """Generate single round-robin fixtures (each pair plays once)."""
    n = len(participants)
    if n < 2:
        raise ValueError('Round-robin requires at least 2 participants.')

    player_ids = [p.user_id for p in participants]
    rounds = _circle_method_schedule(player_ids)
    matches = []
    match_order = 0

    for round_num, round_pairs in enumerate(rounds, start=1):
        for home_id, away_id in round_pairs:
            match_order += 1
            matches.append(Match(
                tournament_id=tournament.id,
                round=f'Round {round_num}',
                match_order=match_order,
                player1_id=home_id,
                player2_id=away_id,
                status='scheduled',
            ))

    return matches


# ---------------------------------------------------------------------------
# Single Elimination
# ---------------------------------------------------------------------------

def _generate_single_elim_fixtures(tournament, participants):
    """Generate single elimination bracket fixtures.

    Handles non-power-of-2 counts with BYEs in round 1.
    """
    n = len(participants)
    if n < 2:
        raise ValueError('Single elimination requires at least 2 participants.')

    player_ids = [p.user_id for p in participants]

    # Find next power of 2
    bracket_size = 1
    while bracket_size < n:
        bracket_size *= 2

    # Pad with BYEs (None)
    seeded = player_ids + [None] * (bracket_size - n)

    matches = []
    match_order = 0
    num_rounds = 0
    temp = bracket_size
    while temp > 1:
        num_rounds += 1
        temp //= 2

    # Generate round 1 matches
    round_matches = []
    for i in range(0, bracket_size, 2):
        match_order += 1
        p1 = seeded[i]
        p2 = seeded[i + 1]

        # If one side is BYE, still create the match (auto-advance later)
        match = Match(
            tournament_id=tournament.id,
            round='Round 1',
            match_order=match_order,
            player1_id=p1,
            player2_id=p2,
            status='scheduled' if (p1 and p2) else 'verified',  # BYE auto-wins
        )
        # Auto-set score for BYE matches
        if p1 and not p2:
            match.score1 = 3
            match.score2 = 0
        elif p2 and not p1:
            match.score1 = 0
            match.score2 = 3

        matches.append(match)
        round_matches.append(match)

    # Generate placeholder matches for subsequent rounds
    round_names = _get_round_names(num_rounds)
    for round_idx in range(1, num_rounds):
        prev_count = len(round_matches)
        next_round_matches = []
        for i in range(0, prev_count, 2):
            match_order += 1
            match = Match(
                tournament_id=tournament.id,
                round=round_names[round_idx],
                match_order=match_order,
                player1_id=None,  # TBD — filled when previous matches verify
                player2_id=None,
                status='scheduled',
            )
            matches.append(match)
            next_round_matches.append(match)
        round_matches = next_round_matches

    return matches


def _get_round_names(num_rounds):
    """Generate round names for single elimination."""
    names = []
    for i in range(num_rounds):
        remaining = num_rounds - i
        if remaining == 1:
            names.append('Final')
        elif remaining == 2:
            names.append('Semi-Final')
        elif remaining == 3:
            names.append('Quarter-Final')
        else:
            names.append(f'Round {i + 1}')
    return names
