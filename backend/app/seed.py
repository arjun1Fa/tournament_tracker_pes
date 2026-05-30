"""Database seeding."""
import logging
from flask import current_app
from .extensions import db
from .models.admin import Admin

logger = logging.getLogger(__name__)


def seed_admin():
    """Seed the admin account if it does not exist."""
    email = current_app.config['ADMIN_EMAIL']
    username = current_app.config['ADMIN_USERNAME']
    password = current_app.config['ADMIN_PASSWORD']

    admin = Admin.query.filter_by(username=username).first()
    if not admin:
        logger.info(f"Seeding admin user '{username}'...")
        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
    else:
        logger.info(f"Admin user '{username}' already exists — skipping seed.")
