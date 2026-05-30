"""Blueprint registration."""


def register_blueprints(app):
    """Register all route blueprints with the Flask app."""
    from .auth import auth_bp
    from .tournaments import tournaments_bp
    from .matches import matches_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tournaments_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(admin_bp)
