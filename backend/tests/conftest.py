"""Test configuration and fixtures."""
import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def db(app):
    """Create a fresh database for each test."""
    with app.app_context():
        _db.create_all()
        # Seed admin after tables are created
        from app.seed import seed_admin
        seed_admin()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def admin_headers(client):
    """Login as admin and return auth headers."""
    # Admin is seeded in create_app
    response = client.post('/api/auth/login', json={
        'email': 'winternx135@gmail.com',
        'password': 'testadminpass',
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def player_headers(client):
    """Register a test player and return auth headers."""
    response = client.post('/api/auth/register', json={
        'email': 'player@test.com',
        'password': 'testpass123',
        'username': 'TestPlayer',
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
