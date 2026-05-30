"""Seed the admin user on first run."""
from flask import current_app

from .extensions import db
from .models.user import User


def seed_admin():
    """Create the WinterFA admin account if it doesn't exist.

    Reads ADMIN_PASSWORD from app config (set via environment variable).
    This ensures the admin account is always available after deployment.
    """
    admin = User.query.filter_by(username=current_app.config['ADMIN_USERNAME']).first()
    if admin is None:
        admin = User(
            email=current_app.config['ADMIN_EMAIL'],
            username=current_app.config['ADMIN_USERNAME'],
            is_admin=True,
        )
        admin.set_password(current_app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()
        current_app.logger.info(
            f"Admin user '{admin.username}' seeded successfully."
        )
    else:
        current_app.logger.info(
            f"Admin user '{admin.username}' already exists — skipping seed."
        )
