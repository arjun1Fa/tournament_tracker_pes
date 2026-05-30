"""Tests for admin routes."""


class TestAdminUsers:
    """Tests for admin user management."""

    def test_list_users(self, client, admin_headers):
        """Admin can list all users."""
        response = client.get('/api/admin/users', headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert data['total'] >= 1  # At least the admin

    def test_list_users_non_admin(self, client, player_headers):
        """Non-admin gets 403."""
        response = client.get('/api/admin/users', headers=player_headers)
        assert response.status_code == 403

    def test_list_users_no_auth(self, client):
        """No auth gets 401."""
        response = client.get('/api/admin/users')
        assert response.status_code == 401

    def test_suspend_user(self, client, admin_headers):
        """Admin can suspend a player."""
        # Register a player
        reg = client.post('/api/auth/register', json={
            'email': 'suspend_me@test.com', 'password': 'testpass123', 'username': 'SuspendMe',
        })
        user_id = reg.get_json()['user']['id']

        # Suspend
        response = client.patch(f'/api/admin/users/{user_id}/suspend', headers=admin_headers)
        assert response.status_code == 200
        assert response.get_json()['user']['is_suspended'] is True

        # Toggle back
        response = client.patch(f'/api/admin/users/{user_id}/suspend', headers=admin_headers)
        assert response.status_code == 200
        assert response.get_json()['user']['is_suspended'] is False

    def test_cannot_suspend_admin(self, client, admin_headers, db):
        """Cannot suspend the admin account."""
        from app.models.user import User
        admin = User.query.filter_by(is_admin=True).first()

        response = client.patch(f'/api/admin/users/{admin.id}/suspend', headers=admin_headers)
        assert response.status_code == 400

    def test_ban_user(self, client, admin_headers):
        """Admin can ban (delete) a player."""
        reg = client.post('/api/auth/register', json={
            'email': 'ban_me@test.com', 'password': 'testpass123', 'username': 'BanMe',
        })
        user_id = reg.get_json()['user']['id']

        response = client.delete(f'/api/admin/users/{user_id}/ban', headers=admin_headers)
        assert response.status_code == 200

        # Verify user is gone
        from app.models.user import User
        assert User.query.get(user_id) is None

    def test_search_users(self, client, admin_headers):
        """Admin can search users by username."""
        client.post('/api/auth/register', json={
            'email': 'searchable@test.com', 'password': 'testpass123', 'username': 'SearchableUser',
        })
        response = client.get('/api/admin/users?search=Searchable', headers=admin_headers)
        assert response.status_code == 200
        users = response.get_json()['users']
        assert any(u['username'] == 'SearchableUser' for u in users)


class TestAdminTournaments:
    """Tests for admin tournament management."""

    def test_list_all_tournaments(self, client, admin_headers, player_headers):
        """Admin sees all tournaments including private."""
        # Create a private tournament
        client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Secret League', 'is_public': False, 'format': 'efl',
        })
        response = client.get('/api/admin/tournaments', headers=admin_headers)
        assert response.status_code == 200
        tournaments = response.get_json()['tournaments']
        assert any(t['name'] == 'Secret League' for t in tournaments)

    def test_edit_tournament(self, client, admin_headers, player_headers):
        """Admin can edit any tournament."""
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Editable', 'format': 'efl',
        })
        tid = create_resp.get_json()['tournament']['id']

        response = client.patch(f'/api/admin/tournaments/{tid}', headers=admin_headers, json={
            'name': 'Edited Name',
            'max_participants': 20,
        })
        assert response.status_code == 200
        assert response.get_json()['tournament']['name'] == 'Edited Name'

    def test_delete_tournament(self, client, admin_headers, player_headers):
        """Admin can delete a tournament."""
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Deletable', 'format': 'efl',
        })
        tid = create_resp.get_json()['tournament']['id']

        response = client.delete(f'/api/admin/tournaments/{tid}', headers=admin_headers)
        assert response.status_code == 200


class TestAdminDispute:
    """Tests for admin dispute resolution."""

    def test_resolve_disputed_match(self, client, admin_headers, db):
        """Admin resolves a disputed match."""
        # Setup: create tournament, 2 players, start, report, dispute
        reg1 = client.post('/api/auth/register', json={
            'email': 'disp1@test.com', 'password': 'testpass123', 'username': 'Disp1',
        })
        p1_headers = {'Authorization': f'Bearer {reg1.get_json()["access_token"]}'}

        create_resp = client.post('/api/tournaments', headers=p1_headers, json={
            'name': 'Dispute Test', 'format': 'round_robin', 'max_participants': 2,
        })
        tid = create_resp.get_json()['tournament']['id']

        reg2 = client.post('/api/auth/register', json={
            'email': 'disp2@test.com', 'password': 'testpass123', 'username': 'Disp2',
        })
        p2_headers = {'Authorization': f'Bearer {reg2.get_json()["access_token"]}'}
        client.post(f'/api/tournaments/{tid}/join', headers=p2_headers)
        client.post(f'/api/tournaments/{tid}/start', headers=p1_headers)

        matches_resp = client.get(f'/api/tournaments/{tid}/matches')
        match_id = list(matches_resp.get_json()['rounds'].values())[0][0]['id']

        # Report
        client.post(f'/api/matches/{match_id}/report', headers=p1_headers, json={
            'team1_name': 'A', 'team2_name': 'B', 'score1': 2, 'score2': 1,
            'my_team': 'team1',
            'team1_stats': {'possession': 55, 'shots': 6, 'shots_on_target': 4,
                            'fouls': 1, 'offsides': 0, 'corner_kicks': 2,
                            'free_kicks': 1, 'passes': 150, 'successful_passes': 120,
                            'crosses': 3, 'interceptions': 10, 'tackles': 7, 'saves': 1},
            'team2_stats': {'possession': 45, 'shots': 3, 'shots_on_target': 1,
                            'fouls': 2, 'offsides': 1, 'corner_kicks': 0,
                            'free_kicks': 2, 'passes': 100, 'successful_passes': 75,
                            'crosses': 1, 'interceptions': 5, 'tackles': 4, 'saves': 3},
        })

        # Dispute
        client.post(f'/api/matches/{match_id}/verify', headers=p2_headers, json={
            'confirmed': False,
        })

        # Admin resolves
        response = client.post(f'/api/admin/matches/{match_id}/resolve', headers=admin_headers, json={
            'score1': 2, 'score2': 1,
        })
        assert response.status_code == 200
        assert response.get_json()['match']['status'] == 'verified'
        assert response.get_json()['match']['admin_resolved'] is True


class TestAdminAnalytics:
    """Tests for admin analytics."""

    def test_analytics(self, client, admin_headers):
        """Admin can view analytics."""
        response = client.get('/api/admin/analytics', headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_users' in data
        assert 'total_tournaments' in data
        assert 'total_matches' in data

    def test_analytics_non_admin(self, client, player_headers):
        """Non-admin cannot view analytics."""
        response = client.get('/api/admin/analytics', headers=player_headers)
        assert response.status_code == 403
