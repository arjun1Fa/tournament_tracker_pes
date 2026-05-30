"""Blueprint registration."""
from flask import Flask


def register_blueprints(app: Flask):
    from .auth import auth_bp
    from .public import public_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
