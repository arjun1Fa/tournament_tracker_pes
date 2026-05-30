"""Flask extension instances.

Initialized here without binding to an app (deferred init pattern).
Bound to the app in create_app() via .init_app(app).
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
