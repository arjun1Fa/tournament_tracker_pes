"""Tests for authentication routes."""


class TestRegister:
    """Tests for POST /api/auth/register."""

    def test_register_success(self, client):
        """Successful registration returns 201 with tokens."""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@test.com',
            'password': 'password123',
            'username': 'NewUser',
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == 'NewUser'
        assert data['user']['is_admin'] is False

    def test_register_duplicate_email(self, client):
        """Duplicate email returns 409."""
        client.post('/api/auth/register', json={
            'email': 'dup@test.com',
            'password': 'password123',
            'username': 'User1',
        })
        response = client.post('/api/auth/register', json={
            'email': 'dup@test.com',
            'password': 'password123',
            'username': 'User2',
        })
        assert response.status_code == 409

    def test_register_duplicate_username(self, client):
        """Duplicate username returns 409."""
        client.post('/api/auth/register', json={
            'email': 'user1@test.com',
            'password': 'password123',
            'username': 'SameName',
        })
        response = client.post('/api/auth/register', json={
            'email': 'user2@test.com',
            'password': 'password123',
            'username': 'SameName',
        })
        assert response.status_code == 409

    def test_register_invalid_email(self, client):
        """Invalid email returns 400."""
        response = client.post('/api/auth/register', json={
            'email': 'not-an-email',
            'password': 'password123',
            'username': 'ValidUser',
        })
        assert response.status_code == 400

    def test_register_short_password(self, client):
        """Password too short returns 400."""
        response = client.post('/api/auth/register', json={
            'email': 'valid@test.com',
            'password': 'short',
            'username': 'ValidUser',
        })
        assert response.status_code == 400

    def test_register_invalid_username(self, client):
        """Invalid username returns 400."""
        response = client.post('/api/auth/register', json={
            'email': 'valid@test.com',
            'password': 'password123',
            'username': 'ab',  # Too short
        })
        assert response.status_code == 400

    def test_register_cannot_set_admin(self, client):
        """Registration never creates an admin, even if is_admin is sent."""
        response = client.post('/api/auth/register', json={
            'email': 'sneaky@test.com',
            'password': 'password123',
            'username': 'SneakyUser',
            'is_admin': True,  # Should be ignored
        })
        assert response.status_code == 201
        assert response.get_json()['user']['is_admin'] is False


class TestLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client):
        """Valid credentials return 200 with tokens."""
        # Register first
        client.post('/api/auth/register', json={
            'email': 'login@test.com',
            'password': 'password123',
            'username': 'LoginUser',
        })
        # Login
        response = client.post('/api/auth/login', json={
            'email': 'login@test.com',
            'password': 'password123',
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_login_wrong_password(self, client):
        """Wrong password returns 401."""
        client.post('/api/auth/register', json={
            'email': 'wrong@test.com',
            'password': 'password123',
            'username': 'WrongPwUser',
        })
        response = client.post('/api/auth/login', json={
            'email': 'wrong@test.com',
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Nonexistent email returns 401."""
        response = client.post('/api/auth/login', json={
            'email': 'ghost@test.com',
            'password': 'password123',
        })
        assert response.status_code == 401

    def test_login_admin(self, client):
        """Admin login returns is_admin=True."""
        response = client.post('/api/auth/login', json={
            'email': 'winternx135@gmail.com',
            'password': 'testadminpass',
        })
        assert response.status_code == 200
        assert response.get_json()['user']['is_admin'] is True

    def test_login_suspended_user(self, client, db):
        """Suspended user cannot login."""
        from app.models.user import User
        # Register
        client.post('/api/auth/register', json={
            'email': 'suspended@test.com',
            'password': 'password123',
            'username': 'SuspendedUser',
        })
        # Suspend the user directly in DB
        user = User.query.filter_by(email='suspended@test.com').first()
        user.is_suspended = True
        db.session.commit()
        # Try login
        response = client.post('/api/auth/login', json={
            'email': 'suspended@test.com',
            'password': 'password123',
        })
        assert response.status_code == 403


class TestMe:
    """Tests for GET /api/auth/me."""

    def test_me_authenticated(self, client, player_headers):
        """Authenticated user gets their profile."""
        response = client.get('/api/auth/me', headers=player_headers)
        assert response.status_code == 200
        assert response.get_json()['user']['username'] == 'TestPlayer'

    def test_me_no_token(self, client):
        """No token returns 401."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401

    def test_me_admin(self, client, admin_headers):
        """Admin sees is_admin=True."""
        response = client.get('/api/auth/me', headers=admin_headers)
        assert response.status_code == 200
        assert response.get_json()['user']['is_admin'] is True


class TestRefresh:
    """Tests for POST /api/auth/refresh."""

    def test_refresh_success(self, client):
        """Valid refresh token returns new access token."""
        # Register
        reg = client.post('/api/auth/register', json={
            'email': 'refresh@test.com',
            'password': 'password123',
            'username': 'RefreshUser',
        })
        refresh_token = reg.get_json()['refresh_token']
        # Refresh
        response = client.post('/api/auth/refresh', headers={
            'Authorization': f'Bearer {refresh_token}',
        })
        assert response.status_code == 200
        assert 'access_token' in response.get_json()


class TestDeviceToken:
    """Tests for POST /api/auth/device-token."""

    def test_register_device_token(self, client, player_headers):
        """Register FCM token succeeds."""
        response = client.post('/api/auth/device-token', headers=player_headers, json={
            'fcm_token': 'fake-fcm-token-12345',
            'platform': 'android',
        })
        assert response.status_code == 200

    def test_register_device_token_invalid_platform(self, client, player_headers):
        """Invalid platform returns 400."""
        response = client.post('/api/auth/device-token', headers=player_headers, json={
            'fcm_token': 'fake-token',
            'platform': 'windows',
        })
        assert response.status_code == 400


class TestUpdateProfile:
    """Tests for PATCH /api/auth/profile."""

    def test_update_profile(self, client, player_headers):
        """Update profile fields."""
        response = client.patch('/api/auth/profile', headers=player_headers, json={
            'platform': 'PS5',
            'favourite_club': 'FC Barcelona',
        })
        assert response.status_code == 200
        data = response.get_json()['user']
        assert data['platform'] == 'PS5'
        assert data['favourite_club'] == 'FC Barcelona'
