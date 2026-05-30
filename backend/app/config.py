"""Flask application configuration classes.

All environments connect to Supabase PostgreSQL via DATABASE_URL.
"""
import os
from datetime import timedelta


class BaseConfig:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-fallback-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Admin seed
    ADMIN_EMAIL = 'winternx135@gmail.com'
    ADMIN_USERNAME = 'WinterFA'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin-change-me')

    # Firebase
    FIREBASE_CREDENTIALS_JSON = os.environ.get(
        'FIREBASE_CREDENTIALS_JSON', 'firebase-service-account.json'
    )


class DevelopmentConfig(BaseConfig):
    """Development configuration — connects to Supabase PostgreSQL."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///dev_fallback.db'  # Fallback only if DATABASE_URL not set
    )


class ProductionConfig(BaseConfig):
    """Production configuration — Supabase PostgreSQL on Render."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(BaseConfig):
    """Testing configuration — in-memory SQLite for fast tests."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-secret-key'
    ADMIN_PASSWORD = 'testadminpass'


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
