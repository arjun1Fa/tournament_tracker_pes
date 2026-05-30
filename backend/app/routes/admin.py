"""Admin routes — user management, dispute resolution, analytics.

All endpoints require @admin_required (checks JWT is_admin claim).
Only the WinterFA account has this flag.
"""
from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models.user import User
from ..models.tournament import Tournament, TournamentParticipant
from ..models.match import Match
from ..models.match_stats import MatchStats
from ..services.match_service import STAT_FIELDS, _fill_stats
from ..utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (paginated).

    Query params: page, per_page, search (username/email substring)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()

    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'users': [u.to_dict(include_email=True) for u in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200


@admin_bp.route('/users/<int:user_id>/suspend', methods=['PATCH'])
@admin_required
def suspend_user(user_id):
    """Toggle user suspension."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if user.is_admin:
        return jsonify({'error': 'Cannot suspend admin.'}), 400

    user.is_suspended = not user.is_suspended
    db.session.commit()

    action = 'suspended' if user.is_suspended else 'unsuspended'
    return jsonify({
        'message': f'User {user.username} {action}.',
        'user': user.to_dict(include_email=True),
    }), 200


@admin_bp.route('/users/<int:user_id>/ban', methods=['DELETE'])
@admin_required
def ban_user(user_id):
    """Permanently ban (delete) a user."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if user.is_admin:
        return jsonify({'error': 'Cannot ban admin.'}), 400

    username = user.username
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': f'User {username} has been banned and deleted.'}), 200


# ---------------------------------------------------------------------------
# Tournament Management
# ---------------------------------------------------------------------------

@admin_bp.route('/tournaments', methods=['GET'])
@admin_required
def list_all_tournaments():
    """List ALL tournaments (including private)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')

    query = Tournament.query
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Tournament.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tournaments': [t.to_dict(include_participants=True) for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200


@admin_bp.route('/tournaments/<int:tournament_id>', methods=['PATCH'])
@admin_required
def edit_tournament(tournament_id):
    """Edit any tournament field."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required.'}), 400

    allowed_fields = ['name', 'is_public', 'max_participants', 'status', 'rules']
    for field in allowed_fields:
        if field in data:
            setattr(tournament, field, data[field])

    # Handle password change
    if 'password' in data:
        if data['password']:
            tournament.set_password(data['password'])
        else:
            tournament.password_hash = None

    db.session.commit()

    return jsonify({
        'message': 'Tournament updated.',
        'tournament': tournament.to_dict(),
    }), 200


@admin_bp.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
@admin_required
def delete_tournament(tournament_id):
    """Delete a tournament and all associated matches (cascade)."""
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        return jsonify({'error': 'Tournament not found.'}), 404

    name = tournament.name
    db.session.delete(tournament)
    db.session.commit()

    return jsonify({'message': f'Tournament "{name}" deleted.'}), 200


# ---------------------------------------------------------------------------
# Dispute Resolution
# ---------------------------------------------------------------------------

@admin_bp.route('/matches/<int:match_id>/resolve', methods=['POST'])
@admin_required
def resolve_match(match_id):
    """Admin resolves a disputed match by overriding the result.

    Body: {
        "score1": int,
        "score2": int,
        "team1_stats": { ... },  (optional — override stats)
        "team2_stats": { ... }   (optional)
    }
    """
    match = db.session.get(Match, match_id)
    if not match:
        return jsonify({'error': 'Match not found.'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required.'}), 400

    # Override scores
    if 'score1' in data:
        match.score1 = int(data['score1'])
    if 'score2' in data:
        match.score2 = int(data['score2'])

    # Override stats if provided
    if 'team1_stats' in data:
        stat1 = MatchStats.query.filter_by(
            match_id=match_id, user_id=match.player1_id
        ).first()
        if stat1:
            _fill_stats(stat1, data['team1_stats'])

    if 'team2_stats' in data:
        stat2 = MatchStats.query.filter_by(
            match_id=match_id, user_id=match.player2_id
        ).first()
        if stat2:
            _fill_stats(stat2, data['team2_stats'])

    match.status = 'verified'
    match.admin_resolved = True
    match.verified_by_player1 = True
    match.verified_by_player2 = True
    db.session.commit()

    # Advance winner in knockout if applicable
    knockout_rounds = ['Qualification Round', 'Semi-Final', 'Grand Final',
                       'Quarter-Final', 'Round 1', 'Final']
    if match.round in knockout_rounds:
        from ..services.match_service import advance_winner
        advance_winner(match)

    return jsonify({
        'message': 'Match resolved by admin.',
        'match': match.to_dict(include_stats=True),
    }), 200


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
def get_analytics():
    """Cross-tournament analytics dashboard."""
    total_users = User.query.count()
    total_tournaments = Tournament.query.count()
    total_matches = Match.query.count()
    verified_matches = Match.query.filter_by(status='verified').count()
    disputed_matches = Match.query.filter_by(status='disputed').count()

    # Average goals per match
    verified = Match.query.filter(
        Match.status == 'verified',
        Match.score1.isnot(None),
        Match.score2.isnot(None),
    ).all()

    total_goals = sum((m.score1 or 0) + (m.score2 or 0) for m in verified)
    avg_goals = round(total_goals / len(verified), 2) if verified else 0

    # Most active players (by matches played)
    from sqlalchemy import func
    active_players = db.session.query(
        User.username,
        func.count(Match.id).label('match_count'),
    ).join(
        Match, db.or_(Match.player1_id == User.id, Match.player2_id == User.id)
    ).filter(
        Match.status == 'verified',
    ).group_by(User.username).order_by(func.count(Match.id).desc()).limit(10).all()

    return jsonify({
        'total_users': total_users,
        'total_tournaments': total_tournaments,
        'total_matches': total_matches,
        'verified_matches': verified_matches,
        'disputed_matches': disputed_matches,
        'total_goals': total_goals,
        'avg_goals_per_match': avg_goals,
        'most_active_players': [
            {'username': u, 'matches_played': c} for u, c in active_players
        ],
    }), 200
