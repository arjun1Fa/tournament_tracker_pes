"""Custom decorators for route protection."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def admin_required(fn):
    """Decorator that ensures the current user is an admin.

    Must be used on routes that already require JWT authentication.
    Checks the 'is_admin' claim in the JWT payload.
    Returns 403 Forbidden if the user is not an admin.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if not claims.get('is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
