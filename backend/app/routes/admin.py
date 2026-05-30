"""Admin management routes — JWT protected."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.tournament import Tournament
from ..models.player import Player
from ..models.match import Match
from ..services.fixture_service import generate_round_robin, generate_playoff_bracket, advance_playoff_winner
from ..services.standings_service import compute_standings

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ── Tournaments ──────────────────────────────────────────────────────────────

@admin_bp.route('/tournaments', methods=['POST'])
@jwt_required()
def create_tournament():
    """Create a new tournament."""
    data = request.get_json()
    name = (data or {}).get('name', '').strip()
    if not name:
        return jsonify({'error': 'Tournament name is required.'}), 400

    tournament = Tournament(name=name, status='registration')
    db.session.add(tournament)
    db.session.commit()
    return jsonify({'tournament': tournament.to_dict()}), 201


@admin_bp.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
@jwt_required()
def delete_tournament(tournament_id):
    """Delete a tournament and all its data."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    db.session.delete(tournament)
    db.session.commit()
    return jsonify({'message': 'Tournament deleted.'}), 200


@admin_bp.route('/tournaments/<int:tournament_id>/start', methods=['POST'])
@jwt_required()
def start_tournament(tournament_id):
    """Generate all round-robin league fixtures."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    if tournament.status != 'registration':
        return jsonify({'error': 'Tournament is already started.'}), 400

    players = Player.query.filter_by(tournament_id=tournament_id).all()
    if len(players) < 2:
        return jsonify({'error': 'Need at least 2 players to start.'}), 400

    try:
        matches = generate_round_robin(tournament, players)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    for m in matches:
        db.session.add(m)

    tournament.status = 'league_ongoing'
    db.session.commit()

    return jsonify({
        'message': f'Tournament started! {len(matches)} fixtures generated.',
        'tournament': tournament.to_dict(),
    }), 200


@admin_bp.route('/tournaments/<int:tournament_id>/start_playoffs', methods=['POST'])
@jwt_required()
def start_playoffs(tournament_id):
    """Transition from league to playoffs — generate playoff bracket from top 6."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    if tournament.status != 'league_ongoing':
        return jsonify({'error': 'League stage must be ongoing to start playoffs.'}), 400

    standings = compute_standings(tournament)
    if len(standings) < 6:
        return jsonify({'error': 'Need at least 6 players in standings to start playoffs.'}), 400

    try:
        generate_playoff_bracket(tournament, standings, db.session)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    tournament.status = 'playoffs_ongoing'
    db.session.commit()

    return jsonify({
        'message': 'Playoffs started! Bracket generated.',
        'tournament': tournament.to_dict(),
    }), 200


# ── Players ──────────────────────────────────────────────────────────────────

@admin_bp.route('/tournaments/<int:tournament_id>/players', methods=['POST'])
@jwt_required()
def add_player(tournament_id):
    """Add a player to a tournament."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    if tournament.status != 'registration':
        return jsonify({'error': 'Cannot add players after tournament has started.'}), 400

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Player name is required.'}), 400

    player = Player(
        tournament_id=tournament_id,
        name=name,
        in_game_team_name=data.get('in_game_team_name', '').strip() or None,
        favourite_club=data.get('favourite_club', '').strip() or None,
        team_image_url=data.get('team_image_url', '').strip() or None,
    )
    db.session.add(player)
    db.session.commit()
    return jsonify({'player': player.to_dict()}), 201


@admin_bp.route('/players/<int:player_id>', methods=['PATCH'])
@jwt_required()
def update_player(player_id):
    """Update player details (name, team name, club, image URL)."""
    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({'error': 'Player not found.'}), 404

    data = request.get_json() or {}
    if 'name' in data:
        player.name = data['name'].strip()
    if 'in_game_team_name' in data:
        player.in_game_team_name = data['in_game_team_name'].strip() or None
    if 'favourite_club' in data:
        player.favourite_club = data['favourite_club'].strip() or None
    if 'team_image_url' in data:
        player.team_image_url = data['team_image_url'].strip() or None

    db.session.commit()
    return jsonify({'player': player.to_dict()}), 200


@admin_bp.route('/players/<int:player_id>', methods=['DELETE'])
@jwt_required()
def delete_player(player_id):
    """Delete a player (only during registration)."""
    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({'error': 'Player not found.'}), 404

    tournament = db.session.get(Tournament, player.tournament_id)
    if tournament and tournament.status != 'registration':
        return jsonify({'error': 'Cannot delete players after tournament has started.'}), 400

    db.session.delete(player)
    db.session.commit()
    return jsonify({'message': 'Player deleted.'}), 200


# ── Match Score Input ────────────────────────────────────────────────────────

@admin_bp.route('/matches/<int:match_id>', methods=['PATCH'])
@jwt_required()
def update_match(match_id):
    """Input or update match result and stats."""
    match = db.session.get(Match, match_id)
    if not match:
        return jsonify({'error': 'Match not found.'}), 404

    data = request.get_json() or {}

    # Validate scores
    score1 = data.get('score1')
    score2 = data.get('score2')
    if score1 is None or score2 is None:
        return jsonify({'error': 'score1 and score2 are required.'}), 400

    match.score1 = int(score1)
    match.score2 = int(score2)
    match.possession1 = data.get('possession1')
    match.possession2 = data.get('possession2')
    match.shots1 = data.get('shots1')
    match.shots2 = data.get('shots2')
    match.shots_on_target1 = data.get('shots_on_target1')
    match.shots_on_target2 = data.get('shots_on_target2')
    match.status = 'completed'
    match.completed_at = datetime.now(timezone.utc)

    # If playoff match, advance winner
    if match.stage == 'playoff':
        advance_playoff_winner(match, db.session)

        # Check if this was the final
        if match.round_name == 'Final':
            tournament = db.session.get(Tournament, match.tournament_id)
            if tournament:
                tournament.status = 'completed'

    db.session.commit()
    return jsonify({'match': match.to_dict()}), 200


@admin_bp.route('/tournaments/<int:tournament_id>/matches', methods=['GET'])
@jwt_required()
def get_admin_matches(tournament_id):
    """Get all matches for a tournament (admin view — shows scheduled too)."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    matches = Match.query.filter_by(tournament_id=tournament_id).order_by(
        Match.stage, Match.match_order
    ).all()

    rounds = {}
    for match in matches:
        key = match.round_name
        if key not in rounds:
            rounds[key] = []
        rounds[key].append(match.to_dict())

    return jsonify({'rounds': rounds, 'total_matches': len(matches)}), 200
