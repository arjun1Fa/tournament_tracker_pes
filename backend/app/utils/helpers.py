"""Shared helper utilities."""
import re


def validate_email(email):
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    """Username must be 3-30 chars, alphanumeric + underscores."""
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None


def validate_password(password):
    """Password must be at least 8 characters."""
    return len(password) >= 8
