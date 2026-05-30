"""Authentication routes — register, login, me, refresh, device-token."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from ..extensions import db
from ..models.user import User, DeviceToken
from ..utils.helpers import validate_email, validate_username, validate_password

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new player account.

    Body: { "email": str, "password": str, "username": str }
    Returns: JWT access + refresh tokens.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    username = data.get('username', '').strip()

    # Validation
    errors = {}
    if not email or not validate_email(email):
        errors['email'] = 'A valid email is required.'
    if not username or not validate_username(username):
        errors['username'] = 'Username must be 3-30 characters (letters, numbers, underscores).'
    if not password or not validate_password(password):
        errors['password'] = 'Password must be at least 8 characters.'
    if errors:
        return jsonify({'errors': errors}), 400

    # Check uniqueness
    if User.query.filter_by(email=email).first():
        return jsonify({'errors': {'email': 'Email already registered.'}}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({'errors': {'username': 'Username already taken.'}}), 409

    # Create user (never admin via registration)
    user = User(email=email, username=username, is_admin=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Generate tokens
    additional_claims = {'is_admin': False, 'username': user.username}
    access_token = create_access_token(
        identity=str(user.id), additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user.id), additional_claims=additional_claims
    )

    return jsonify({
        'message': 'Registration successful.',
        'user': user.to_dict(include_email=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return JWT tokens.

    Body: { "email": str, "password": str }
    Returns: JWT access + refresh tokens.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    if user.is_suspended:
        return jsonify({'error': 'Your account has been suspended.'}), 403

    # Generate tokens with admin claim from database (never trust client)
    additional_claims = {'is_admin': user.is_admin, 'username': user.username}
    access_token = create_access_token(
        identity=str(user.id), additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user.id), additional_claims=additional_claims
    )

    return jsonify({
        'message': 'Login successful.',
        'user': user.to_dict(include_email=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Return the current authenticated user's profile.

    Requires: Authorization: Bearer <access_token>
    Returns: User data including is_admin flag.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    return jsonify({'user': user.to_dict(include_email=True)}), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Issue a new access token using a valid refresh token.

    Requires: Authorization: Bearer <refresh_token>
    Returns: New access token.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if user.is_suspended:
        return jsonify({'error': 'Your account has been suspended.'}), 403

    additional_claims = {'is_admin': user.is_admin, 'username': user.username}
    access_token = create_access_token(
        identity=str(user.id), additional_claims=additional_claims
    )

    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/device-token', methods=['POST'])
@jwt_required()
def register_device_token():
    """Register or update a device's FCM token for push notifications.

    Body: { "fcm_token": str, "platform": "ios"|"android" }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    fcm_token = data.get('fcm_token', '').strip()
    platform = data.get('platform', '').strip().lower()

    if not fcm_token:
        return jsonify({'error': 'fcm_token is required.'}), 400
    if platform not in ('ios', 'android'):
        return jsonify({'error': 'platform must be "ios" or "android".'}), 400

    # Upsert: update existing token for this user+platform, or create new
    device = DeviceToken.query.filter_by(user_id=user_id, platform=platform).first()
    if device:
        device.fcm_token = fcm_token
        device.updated_at = datetime.now(timezone.utc)
    else:
        device = DeviceToken(user_id=user_id, fcm_token=fcm_token, platform=platform)
        db.session.add(device)

    db.session.commit()
    return jsonify({'message': 'Device token registered.'}), 200


@auth_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    """Update the current user's profile fields.

    Body: { "profile_picture": str?, "platform": str?, "favourite_club": str? }
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Only allow updating profile fields, never admin/email/password here
    allowed_fields = ['profile_picture', 'platform', 'favourite_club']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify({
        'message': 'Profile updated.',
        'user': user.to_dict(include_email=True),
    }), 200
