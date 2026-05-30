"""Public routes — no authentication required."""
from flask import Blueprint, jsonify

from ..extensions import db
from ..models.tournament import Tournament
from ..models.match import Match
from ..services.standings_service import compute_standings, compute_player_leaderboard

public_bp = Blueprint('public', __name__, url_prefix='/api')


@public_bp.route('/tournaments', methods=['GET'])
def list_tournaments():
    """List all tournaments."""
    tournaments = Tournament.query.order_by(Tournament.created_at.desc()).all()
    return jsonify({'tournaments': [t.to_dict() for t in tournaments]}), 200


@public_bp.route('/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    """Get tournament detail including players."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    return jsonify({'tournament': tournament.to_dict(include_players=True)}), 200


@public_bp.route('/tournaments/<int:tournament_id>/matches', methods=['GET'])
def get_matches(tournament_id):
    """Get all matches grouped by round."""
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

    return jsonify({
        'tournament_id': tournament_id,
        'total_matches': len(matches),
        'rounds': rounds,
    }), 200


@public_bp.route('/tournaments/<int:tournament_id>/standings', methods=['GET'])
def get_standings(tournament_id):
    """Get league standings."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    standings = compute_standings(tournament)
    return jsonify({'standings': standings}), 200


@public_bp.route('/tournaments/<int:tournament_id>/leaderboard', methods=['GET'])
def get_leaderboard(tournament_id):
    """Get player stats leaderboard."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404
    leaderboard = compute_player_leaderboard(tournament)
    return jsonify({'leaderboard': leaderboard}), 200


@public_bp.route('/matches/<int:match_id>', methods=['GET'])
def get_match(match_id):
    """Get single match detail."""
    match = db.session.get(Match, match_id)
    if not match:
        return jsonify({'error': 'Match not found.'}), 404
    return jsonify({'match': match.to_dict()}), 200
