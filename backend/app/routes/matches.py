"""Match routes — report, verify, detail, export."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models.match import Match
from ..services.match_service import report_match, verify_match, advance_winner

matches_bp = Blueprint('matches', __name__, url_prefix='/api/matches')


@matches_bp.route('/<int:match_id>', methods=['GET'])
def get_match(match_id):
    """Get match details including stats if verified."""
    match = db.session.get(Match, match_id)
    if not match:
        return jsonify({'error': 'Match not found.'}), 404

    include_stats = match.status in ('verified', 'pending_verification', 'disputed')
    return jsonify({'match': match.to_dict(include_stats=include_stats)}), 200


@matches_bp.route('/<int:match_id>/report', methods=['POST'])
@jwt_required()
def report_match_route(match_id):
    """Submit OCR-scanned match result.

    Body: {
        "team1_name": str,
        "team2_name": str,
        "score1": int,
        "score2": int,
        "my_team": "team1" | "team2",
        "team1_stats": { possession, shots, shots_on_target, ... },
        "team2_stats": { possession, shots, shots_on_target, ... }
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required.'}), 400

    result, error, status_code = report_match(match_id, user_id, data)

    if error:
        return jsonify({'error': error}), status_code

    # Trigger push notification to opponent
    match = db.session.get(Match, match_id)
    if match:
        opponent_id = match.player2_id if user_id == match.player1_id else match.player1_id
        try:
            from ..services.notification_service import send_verification_request
            send_verification_request(opponent_id, match_id)
        except Exception:
            pass  # Don't fail the request if notification fails

    return jsonify({
        'message': 'Match reported. Waiting for opponent verification.',
        'match': result,
    }), 200


@matches_bp.route('/<int:match_id>/verify', methods=['POST'])
@jwt_required()
def verify_match_route(match_id):
    """Opponent verifies or disputes a match result.

    Body: {
        "my_team": "team1" | "team2",
        "confirmed": bool
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required.'}), 400

    result, error, status_code = verify_match(match_id, user_id, data)

    if error:
        return jsonify({'error': error}), status_code

    # If match is now verified, check for knockout advancement
    match = db.session.get(Match, match_id)
    if match and match.status == 'verified':
        knockout_rounds = ['Qualification Round', 'Semi-Final', 'Grand Final',
                           'Quarter-Final', 'Round 1', 'Final']
        if match.round in knockout_rounds:
            advance_winner(match)

    # If disputed, notify admin
    if match and match.status == 'disputed':
        try:
            from ..services.notification_service import send_dispute_notification
            from ..models.user import User
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                send_dispute_notification(admin.id, match_id)
        except Exception:
            pass

    status_msg = 'Match verified!' if match.status == 'verified' else 'Match disputed. Admin will review.'
    return jsonify({
        'message': status_msg,
        'match': result,
    }), 200


@matches_bp.route('/<int:match_id>/export', methods=['GET'])
def export_match(match_id):
    """Export match data as a shareable report card (JSON format).

    The Flutter app renders this into a visual card for sharing.
    """
    match = db.session.get(Match, match_id)
    if not match:
        return jsonify({'error': 'Match not found.'}), 404

    if match.status != 'verified':
        return jsonify({'error': 'Only verified matches can be exported.'}), 400

    stats = [s.to_dict() for s in match.stats]

    report_card = {
        'match_id': match.id,
        'tournament_id': match.tournament_id,
        'tournament_name': match.tournament.name if match.tournament else None,
        'round': match.round,
        'team1_name': match.team1_name,
        'team2_name': match.team2_name,
        'score1': match.score1,
        'score2': match.score2,
        'player1_username': match.player1.username if match.player1 else None,
        'player2_username': match.player2.username if match.player2 else None,
        'stats': stats,
        'headline': f'{match.team1_name} {match.score1}-{match.score2} {match.team2_name}',
    }

    return jsonify({'report_card': report_card}), 200
