"""Admin authentication route — login only."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from ..models.admin import Admin

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Admin login. Returns JWT access token."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required.'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    admin = Admin.query.filter_by(username=username).first()
    if not admin or not admin.check_password(password):
        return jsonify({'error': 'Invalid credentials.'}), 401

    token = create_access_token(identity=str(admin.id), additional_claims={'is_admin': True})
    return jsonify({
        'message': 'Login successful.',
        'access_token': token,
        'admin': {'id': admin.id, 'username': admin.username},
    }), 200
