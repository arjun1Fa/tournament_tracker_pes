"""Flask application factory."""
import os
from flask import Flask

from .config import config_map
from .extensions import db, migrate, jwt, cors


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Defaults to FLASK_ENV environment variable.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from .routes import register_blueprints
    register_blueprints(app)

    # Seed admin user on first run
    with app.app_context():
        from .seed import seed_admin
        # Only seed if tables exist (after migration)
        try:
            seed_admin()
        except Exception:
            # Tables don't exist yet (pre-migration) — skip silently
            pass

    return app
