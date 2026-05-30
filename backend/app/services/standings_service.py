"""Standings, stat leaders, and MVP calculation service.

Implements EFL rulebook tiebreakers (Art. 04):
    1. Goal Difference (GD)
    2. Goals Scored (GF)
    3. Head-to-Head record
"""
from collections import defaultdict

from ..extensions import db
from ..models.match import Match
from ..models.match_stats import MatchStats


def compute_standings(tournament):
    """Compute league standings for a tournament.

    Returns a list of player standings sorted by rank, each containing:
        user_id, username, mp, w, d, l, gf, ga, gd, pts, form

    Args:
        tournament: Tournament model instance.

    Returns:
        List of dicts sorted by EFL tiebreaker rules.
    """
    # Get all verified matches (league phase only — exclude knockout)
    matches = Match.query.filter(
        Match.tournament_id == tournament.id,
        Match.status == 'verified',
        ~Match.round.in_(['Qualification Round', 'Semi-Final', 'Grand Final']),
    ).all()

    # Get scoring rules
    rules = tournament.rules or {}
    win_pts = rules.get('win_points', 3)
    draw_pts = rules.get('draw_points', 1)
    loss_pts = rules.get('loss_points', 0)

    # Build stats per player
    stats = defaultdict(lambda: {
        'mp': 0, 'w': 0, 'd': 0, 'l': 0,
        'gf': 0, 'ga': 0, 'gd': 0, 'pts': 0,
        'results': [],  # For form calculation
    })

    # Head-to-head data for tiebreaking
    h2h = defaultdict(lambda: defaultdict(lambda: {'pts': 0, 'gf': 0, 'ga': 0}))

    for match in matches:
        if match.score1 is None or match.score2 is None:
            continue

        p1 = match.player1_id
        p2 = match.player2_id
        s1 = match.score1
        s2 = match.score2

        # Player 1 stats
        stats[p1]['mp'] += 1
        stats[p1]['gf'] += s1
        stats[p1]['ga'] += s2

        # Player 2 stats
        stats[p2]['mp'] += 1
        stats[p2]['gf'] += s2
        stats[p2]['ga'] += s1

        if s1 > s2:
            # Player 1 wins
            stats[p1]['w'] += 1
            stats[p1]['pts'] += win_pts
            stats[p1]['results'].append('W')

            stats[p2]['l'] += 1
            stats[p2]['pts'] += loss_pts
            stats[p2]['results'].append('L')

            h2h[p1][p2]['pts'] += win_pts
            h2h[p2][p1]['pts'] += loss_pts
        elif s1 < s2:
            # Player 2 wins
            stats[p2]['w'] += 1
            stats[p2]['pts'] += win_pts
            stats[p2]['results'].append('W')

            stats[p1]['l'] += 1
            stats[p1]['pts'] += loss_pts
            stats[p1]['results'].append('L')

            h2h[p2][p1]['pts'] += win_pts
            h2h[p1][p2]['pts'] += loss_pts
        else:
            # Draw
            stats[p1]['d'] += 1
            stats[p1]['pts'] += draw_pts
            stats[p1]['results'].append('D')

            stats[p2]['d'] += 1
            stats[p2]['pts'] += draw_pts
            stats[p2]['results'].append('D')

            h2h[p1][p2]['pts'] += draw_pts
            h2h[p2][p1]['pts'] += draw_pts

        # Head-to-head goals
        h2h[p1][p2]['gf'] += s1
        h2h[p1][p2]['ga'] += s2
        h2h[p2][p1]['gf'] += s2
        h2h[p2][p1]['ga'] += s1

    # Calculate GD
    for uid in stats:
        stats[uid]['gd'] = stats[uid]['gf'] - stats[uid]['ga']

    # Get usernames
    from ..models.user import User
    user_ids = list(stats.keys())
    users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}

    # Also include participants with zero matches
    from ..models.tournament import TournamentParticipant
    all_participants = TournamentParticipant.query.filter_by(
        tournament_id=tournament.id
    ).all()
    for p in all_participants:
        if p.user_id not in stats:
            stats[p.user_id] = {
                'mp': 0, 'w': 0, 'd': 0, 'l': 0,
                'gf': 0, 'ga': 0, 'gd': 0, 'pts': 0,
                'results': [],
            }
        if p.user_id not in users:
            users[p.user_id] = p.user.username if p.user else f'User {p.user_id}'

    # Build standings list
    standings = []
    for uid, s in stats.items():
        standings.append({
            'user_id': uid,
            'username': users.get(uid, f'User {uid}'),
            'mp': s['mp'],
            'w': s['w'],
            'd': s['d'],
            'l': s['l'],
            'gf': s['gf'],
            'ga': s['ga'],
            'gd': s['gd'],
            'pts': s['pts'],
            'form': ''.join(s['results'][-5:]),  # Last 5 results
        })

    # Sort by EFL tiebreaker rules (Art. 04):
    # 1. Points (desc)
    # 2. Goal Difference (desc)
    # 3. Goals Scored (desc)
    # 4. Head-to-Head points (desc)
    def sort_key(entry):
        uid = entry['user_id']
        # H2H against all tied opponents — simplified to total H2H points
        h2h_pts = sum(h2h[uid][opp]['pts'] for opp in h2h[uid])
        h2h_gd = sum(h2h[uid][opp]['gf'] - h2h[uid][opp]['ga'] for opp in h2h[uid])
        h2h_gf = sum(h2h[uid][opp]['gf'] for opp in h2h[uid])
        return (entry['pts'], entry['gd'], entry['gf'], h2h_pts, h2h_gd, h2h_gf)

    standings.sort(key=sort_key, reverse=True)

    # Add rank
    for i, entry in enumerate(standings):
        entry['rank'] = i + 1

    return standings


def compute_stat_leaders(tournament_id):
    """Compute stat leaders across all verified matches in a tournament.

    Returns top 5 players for each stat category.
    """
    # Get all match stats for verified matches
    stats = db.session.query(MatchStats).join(
        Match, MatchStats.match_id == Match.id
    ).filter(
        Match.tournament_id == tournament_id,
        Match.status == 'verified',
    ).all()

    # Aggregate per user
    user_agg = defaultdict(lambda: {
        'goals': 0, 'clean_sheets': 0,
        'possession_sum': 0.0, 'possession_count': 0,
        'shots': 0, 'shots_on_target': 0, 'fouls': 0,
        'passes': 0, 'successful_passes': 0,
        'tackles': 0, 'interceptions': 0,
        'crosses': 0, 'saves': 0,
        'matches_played': 0,
    })

    # We need to know goals per match to compute clean sheets
    match_scores = {}  # match_id -> {user_id: goals_scored, opponent_goals}
    for stat in stats:
        match = stat.match
        uid = stat.user_id

        if match.id not in match_scores:
            match_scores[match.id] = {}

        # Determine which side this user is on
        if match.player1_id == uid:
            goals_scored = match.score1 or 0
            goals_conceded = match.score2 or 0
        else:
            goals_scored = match.score2 or 0
            goals_conceded = match.score1 or 0

        match_scores[match.id][uid] = {
            'scored': goals_scored,
            'conceded': goals_conceded,
        }

        agg = user_agg[uid]
        agg['goals'] += goals_scored
        agg['matches_played'] += 1

        if goals_conceded == 0:
            agg['clean_sheets'] += 1

        if stat.possession is not None:
            agg['possession_sum'] += stat.possession
            agg['possession_count'] += 1

        agg['shots'] += stat.shots or 0
        agg['shots_on_target'] += stat.shots_on_target or 0
        agg['fouls'] += stat.fouls or 0
        agg['passes'] += stat.passes or 0
        agg['successful_passes'] += stat.successful_passes or 0
        agg['tackles'] += stat.tackles or 0
        agg['interceptions'] += stat.interceptions or 0
        agg['crosses'] += stat.crosses or 0
        agg['saves'] += stat.saves or 0

    # Get usernames
    from ..models.user import User
    user_ids = list(user_agg.keys())
    users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}

    # Build leader boards (top 5 per category)
    categories = {
        'top_scorers': 'goals',
        'most_clean_sheets': 'clean_sheets',
        'most_shots_on_target': 'shots_on_target',
        'most_passes': 'passes',
        'most_successful_passes': 'successful_passes',
        'most_tackles': 'tackles',
        'most_interceptions': 'interceptions',
        'most_saves': 'saves',
    }

    leaders = {}
    for category_name, stat_key in categories.items():
        sorted_users = sorted(
            user_agg.items(),
            key=lambda x: x[1][stat_key],
            reverse=True,
        )[:5]
        leaders[category_name] = [
            {
                'user_id': uid,
                'username': users.get(uid, f'User {uid}'),
                'value': data[stat_key],
            }
            for uid, data in sorted_users
        ]

    # Average possession (special handling)
    possession_leaders = sorted(
        [(uid, data) for uid, data in user_agg.items() if data['possession_count'] > 0],
        key=lambda x: x[1]['possession_sum'] / x[1]['possession_count'],
        reverse=True,
    )[:5]
    leaders['highest_avg_possession'] = [
        {
            'user_id': uid,
            'username': users.get(uid, f'User {uid}'),
            'value': round(data['possession_sum'] / data['possession_count'], 1),
        }
        for uid, data in possession_leaders
    ]

    return leaders


def compute_mvp(tournament_id):
    """Compute MVP rankings using a weighted composite score.

    Weights:
        Goals:              3.0
        Clean Sheets:       2.0
        Goal Difference:    1.0 (per match avg)
        Shots on Target:    0.5
        Tackles + Intercepts: 0.3 each
    """
    # Reuse stat aggregation
    stats = db.session.query(MatchStats).join(
        Match, MatchStats.match_id == Match.id
    ).filter(
        Match.tournament_id == tournament_id,
        Match.status == 'verified',
    ).all()

    user_data = defaultdict(lambda: {
        'goals': 0, 'clean_sheets': 0, 'gd': 0,
        'shots_on_target': 0, 'tackles': 0, 'interceptions': 0,
        'matches': 0,
    })

    for stat in stats:
        match = stat.match
        uid = stat.user_id

        if match.player1_id == uid:
            goals = match.score1 or 0
            conceded = match.score2 or 0
        else:
            goals = match.score2 or 0
            conceded = match.score1 or 0

        data = user_data[uid]
        data['goals'] += goals
        data['gd'] += (goals - conceded)
        data['matches'] += 1

        if conceded == 0:
            data['clean_sheets'] += 1

        data['shots_on_target'] += stat.shots_on_target or 0
        data['tackles'] += stat.tackles or 0
        data['interceptions'] += stat.interceptions or 0

    # Calculate MVP score
    from ..models.user import User
    user_ids = list(user_data.keys())
    users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}

    mvp_list = []
    for uid, data in user_data.items():
        score = (
            data['goals'] * 3.0
            + data['clean_sheets'] * 2.0
            + data['gd'] * 1.0
            + data['shots_on_target'] * 0.5
            + data['tackles'] * 0.3
            + data['interceptions'] * 0.3
        )
        mvp_list.append({
            'user_id': uid,
            'username': users.get(uid, f'User {uid}'),
            'mvp_score': round(score, 1),
            'goals': data['goals'],
            'clean_sheets': data['clean_sheets'],
            'goal_difference': data['gd'],
            'shots_on_target': data['shots_on_target'],
            'tackles': data['tackles'],
            'interceptions': data['interceptions'],
        })

    mvp_list.sort(key=lambda x: x['mvp_score'], reverse=True)

    # Add rank
    for i, entry in enumerate(mvp_list):
        entry['rank'] = i + 1

    return mvp_list
