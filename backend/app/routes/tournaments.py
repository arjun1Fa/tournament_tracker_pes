"""Tournament routes — CRUD, join, start, standings, leaderboard."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models.tournament import Tournament, TournamentParticipant
from ..models.user import User
from ..services.tournament_service import generate_fixtures
from ..services.standings_service import (
    compute_standings,
    compute_stat_leaders,
    compute_mvp,
)

tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/api/tournaments')


@tournaments_bp.route('', methods=['GET'])
def list_tournaments():
    """List tournaments (public by default, filterable).

    Query params: status (open|ongoing|completed), page, per_page
    """
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Tournament.query.filter_by(is_public=True)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Tournament.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tournaments': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200


@tournaments_bp.route('', methods=['POST'])
@jwt_required()
def create_tournament():
    """Create a new tournament.

    Body: {
        "name": str, "is_public": bool, "password": str?,
        "max_participants": int, "format": str, "rules": dict?
    }
    Creator automatically joins as first participant.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Tournament name is required.'}), 400

    is_public = data.get('is_public', True)
    max_participants = data.get('max_participants', 10)
    format_type = data.get('format', 'efl')
    rules = data.get('rules', {})

    # Validate format
    valid_formats = ['round_robin', 'swiss', 'single_elim', 'double_elim', 'group_knockout', 'efl']
    if format_type not in valid_formats:
        return jsonify({'error': f'Invalid format. Must be one of: {", ".join(valid_formats)}'}), 400

    # Create tournament
    tournament = Tournament(
        name=name,
        is_public=is_public,
        max_participants=max_participants,
        format=format_type,
        created_by=user_id,
        rules=rules or _default_rules(format_type),
    )

    # Hash password for private tournaments
    password = data.get('password')
    if not is_public and password:
        tournament.set_password(password)

    db.session.add(tournament)
    db.session.flush()  # Get tournament ID

    # Creator auto-joins as participant #1
    participant = TournamentParticipant(
        tournament_id=tournament.id,
        user_id=user_id,
        seed=1,
    )
    db.session.add(participant)
    db.session.commit()

    return jsonify({
        'message': 'Tournament created.',
        'tournament': tournament.to_dict(include_participants=True),
    }), 201


@tournaments_bp.route('/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    """Get tournament details with participants."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    return jsonify({
        'tournament': tournament.to_dict(include_participants=True),
    }), 200


@tournaments_bp.route('/<int:tournament_id>/join', methods=['POST'])
@jwt_required()
def join_tournament(tournament_id):
    """Join a tournament.

    Body (for private): { "password": str }
    """
    user_id = int(get_jwt_identity())
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    if tournament.status != 'open':
        return jsonify({'error': 'Tournament is not open for registration.'}), 400

    if tournament.participant_count >= tournament.max_participants:
        return jsonify({'error': 'Tournament is full.'}), 400

    # Check if already joined
    existing = TournamentParticipant.query.filter_by(
        tournament_id=tournament_id, user_id=user_id
    ).first()
    if existing:
        return jsonify({'error': 'You have already joined this tournament.'}), 409

    # Check password for private tournaments
    if not tournament.is_public and tournament.password_hash:
        password = request.get_json().get('password', '') if request.get_json() else ''
        if not tournament.check_password(password):
            return jsonify({'error': 'Incorrect tournament password.'}), 403

    # Check if user is suspended
    user = db.session.get(User, user_id)
    if user and user.is_suspended:
        return jsonify({'error': 'Your account is suspended.'}), 403

    participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_id=user_id,
        seed=tournament.participant_count + 1,
    )
    db.session.add(participant)
    db.session.commit()

    return jsonify({
        'message': f'Joined tournament "{tournament.name}".',
        'participant': participant.to_dict(),
    }), 200


@tournaments_bp.route('/<int:tournament_id>/start', methods=['POST'])
@jwt_required()
def start_tournament(tournament_id):
    """Start a tournament — generates all fixtures.

    Only the creator or admin can start.
    """
    user_id = int(get_jwt_identity())
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    if tournament.status != 'open':
        return jsonify({'error': 'Tournament has already started or is completed.'}), 400

    # Only creator or admin can start
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if tournament.created_by != user_id and not claims.get('is_admin', False):
        return jsonify({'error': 'Only the tournament creator or admin can start it.'}), 403

    # Need at least 2 participants
    participant_count = tournament.participant_count
    if participant_count < 2:
        return jsonify({'error': 'Need at least 2 participants to start.'}), 400

    # Generate fixtures based on format
    participants = TournamentParticipant.query.filter_by(
        tournament_id=tournament_id
    ).order_by(TournamentParticipant.seed).all()

    try:
        matches = generate_fixtures(tournament, participants)
        for match in matches:
            db.session.add(match)

        tournament.status = 'ongoing'
        db.session.commit()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({
        'message': 'Tournament started! Fixtures generated.',
        'match_count': len(matches),
        'tournament': tournament.to_dict(),
    }), 200


@tournaments_bp.route('/<int:tournament_id>/matches', methods=['GET'])
def get_tournament_matches(tournament_id):
    """List all fixtures for a tournament, organized by round."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    from ..models.match import Match
    matches = Match.query.filter_by(tournament_id=tournament_id).order_by(
        Match.round, Match.match_order
    ).all()

    # Group by round
    rounds = {}
    for match in matches:
        if match.round not in rounds:
            rounds[match.round] = []
        rounds[match.round].append(match.to_dict())

    return jsonify({
        'tournament_id': tournament_id,
        'total_matches': len(matches),
        'rounds': rounds,
    }), 200


@tournaments_bp.route('/<int:tournament_id>/standings', methods=['GET'])
def get_standings(tournament_id):
    """Get computed standings for a tournament."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    standings = compute_standings(tournament)

    return jsonify({
        'tournament_id': tournament_id,
        'tournament_name': tournament.name,
        'standings': standings,
    }), 200


@tournaments_bp.route('/<int:tournament_id>/leaderboard', methods=['GET'])
def get_leaderboard(tournament_id):
    """Get stat leaders and MVP rankings for a tournament."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    stat_leaders = compute_stat_leaders(tournament_id)
    mvp_rankings = compute_mvp(tournament_id)

    return jsonify({
        'tournament_id': tournament_id,
        'stat_leaders': stat_leaders,
        'mvp_rankings': mvp_rankings,
    }), 200


def _default_rules(format_type):
    """Return default scoring rules for a format."""
    return {
        'win_points': 3,
        'draw_points': 1,
        'loss_points': 0,
        'tiebreakers': ['goal_difference', 'goals_scored', 'head_to_head'],
    }
