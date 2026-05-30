"""Standings computation — Points → GD → Goals Scored."""
from ..models.match import Match


def compute_standings(tournament):
    """Return standings list sorted by points, GD, goals scored.
    
    Returns a list of dicts:
    [{
        'player_id': int,
        'player_name': str,
        'player_team': str,
        'player_image': str,
        'played': int,
        'won': int,
        'drawn': int,
        'lost': int,
        'goals_for': int,
        'goals_against': int,
        'goal_difference': int,
        'points': int,
    }, ...]
    """
    league_matches = Match.query.filter_by(
        tournament_id=tournament.id,
        stage='league',
        status='completed'
    ).all()

    stats = {}

    def init_player(p):
        if p.id not in stats:
            stats[p.id] = {
                'player_id': p.id,
                'player_name': p.name,
                'player_team': p.in_game_team_name,
                'player_image': p.team_image_url,
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goals_for': 0, 'goals_against': 0,
                'goal_difference': 0, 'points': 0,
            }

    for match in league_matches:
        if match.player1 and match.player2:
            init_player(match.player1)
            init_player(match.player2)

            s1 = match.score1 or 0
            s2 = match.score2 or 0

            stats[match.player1_id]['played'] += 1
            stats[match.player2_id]['played'] += 1
            stats[match.player1_id]['goals_for'] += s1
            stats[match.player1_id]['goals_against'] += s2
            stats[match.player2_id]['goals_for'] += s2
            stats[match.player2_id]['goals_against'] += s1

            if s1 > s2:
                stats[match.player1_id]['won'] += 1
                stats[match.player1_id]['points'] += 3
                stats[match.player2_id]['lost'] += 1
            elif s2 > s1:
                stats[match.player2_id]['won'] += 1
                stats[match.player2_id]['points'] += 3
                stats[match.player1_id]['lost'] += 1
            else:
                stats[match.player1_id]['drawn'] += 1
                stats[match.player2_id]['drawn'] += 1
                stats[match.player1_id]['points'] += 1
                stats[match.player2_id]['points'] += 1

    # Also include players who haven't played yet
    from ..models.player import Player
    for player in Player.query.filter_by(tournament_id=tournament.id).all():
        if player.id not in stats:
            stats[player.id] = {
                'player_id': player.id,
                'player_name': player.name,
                'player_team': player.in_game_team_name,
                'player_image': player.team_image_url,
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goals_for': 0, 'goals_against': 0,
                'goal_difference': 0, 'points': 0,
            }

    for s in stats.values():
        s['goal_difference'] = s['goals_for'] - s['goals_against']

    standings = sorted(
        stats.values(),
        key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for'])
    )

    for i, s in enumerate(standings):
        s['position'] = i + 1

    return standings


def compute_player_leaderboard(tournament):
    """Aggregate per-player stats across all completed league matches."""
    from ..models.player import Player

    players = Player.query.filter_by(tournament_id=tournament.id).all()
    player_map = {p.id: p for p in players}

    leaderboard = {pid: {
        'player_id': pid,
        'player_name': p.name,
        'player_team': p.in_game_team_name,
        'player_image': p.team_image_url,
        'total_goals': 0,
        'total_possession_avg': 0.0,
        'total_shots': 0,
        'total_shots_on_target': 0,
        'matches_played': 0,
        'performance_score': 0.0,
    } for pid, p in player_map.items()}

    matches = Match.query.filter_by(
        tournament_id=tournament.id, status='completed'
    ).all()

    for match in matches:
        for slot in [1, 2]:
            pid = match.player1_id if slot == 1 else match.player2_id
            if pid not in leaderboard:
                continue
            lb = leaderboard[pid]
            lb['matches_played'] += 1
            lb['total_goals'] += (match.score1 if slot == 1 else match.score2) or 0
            lb['total_possession_avg'] += (match.possession1 if slot == 1 else match.possession2) or 0
            lb['total_shots'] += (match.shots1 if slot == 1 else match.shots2) or 0
            lb['total_shots_on_target'] += (match.shots_on_target1 if slot == 1 else match.shots_on_target2) or 0
            lb['performance_score'] += match.performance_score(slot)

    result = []
    for lb in leaderboard.values():
        if lb['matches_played'] > 0:
            lb['possession_avg'] = round(lb['total_possession_avg'] / lb['matches_played'], 1)
        else:
            lb['possession_avg'] = 0.0
        result.append(lb)

    return sorted(result, key=lambda x: -x['performance_score'])
