"""Tests for tournament routes."""


class TestCreateTournament:
    """Tests for POST /api/tournaments."""

    def test_create_tournament_success(self, client, player_headers):
        """Successfully create a tournament."""
        response = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'EFL Season I',
            'is_public': True,
            'max_participants': 10,
            'format': 'efl',
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['tournament']['name'] == 'EFL Season I'
        assert data['tournament']['format'] == 'efl'
        assert data['tournament']['participant_count'] == 1  # Creator auto-joined

    def test_create_private_tournament(self, client, player_headers):
        """Create a private tournament with password."""
        response = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Private League',
            'is_public': False,
            'password': 'secret123',
            'max_participants': 8,
            'format': 'round_robin',
        })
        assert response.status_code == 201
        assert response.get_json()['tournament']['has_password'] is True

    def test_create_tournament_no_auth(self, client):
        """Creating without auth fails."""
        response = client.post('/api/tournaments', json={
            'name': 'No Auth League',
        })
        assert response.status_code == 401

    def test_create_tournament_invalid_format(self, client, player_headers):
        """Invalid format returns 400."""
        response = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Bad Format',
            'format': 'invalid_format',
        })
        assert response.status_code == 400


class TestListTournaments:
    """Tests for GET /api/tournaments."""

    def test_list_empty(self, client, db):
        """Empty list when no tournaments."""
        response = client.get('/api/tournaments')
        assert response.status_code == 200
        assert response.get_json()['tournaments'] == []

    def test_list_public_only(self, client, player_headers):
        """Only public tournaments are listed."""
        # Create public
        client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Public League',
            'is_public': True,
            'format': 'efl',
        })
        # Create private
        client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Private League',
            'is_public': False,
            'format': 'efl',
        })
        response = client.get('/api/tournaments')
        data = response.get_json()
        assert len(data['tournaments']) == 1
        assert data['tournaments'][0]['name'] == 'Public League'


class TestJoinTournament:
    """Tests for POST /api/tournaments/<id>/join."""

    def test_join_success(self, client, player_headers):
        """Second player joins a tournament."""
        # Create tournament
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Join Test', 'format': 'efl', 'max_participants': 10,
        })
        tid = create_resp.get_json()['tournament']['id']

        # Register second player
        reg = client.post('/api/auth/register', json={
            'email': 'player2@test.com', 'password': 'testpass123', 'username': 'Player2',
        })
        p2_token = reg.get_json()['access_token']
        p2_headers = {'Authorization': f'Bearer {p2_token}'}

        # Join
        response = client.post(f'/api/tournaments/{tid}/join', headers=p2_headers)
        assert response.status_code == 200

    def test_join_already_joined(self, client, player_headers):
        """Joining twice returns 409."""
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Dup Join', 'format': 'efl',
        })
        tid = create_resp.get_json()['tournament']['id']

        # Creator is already joined, try joining again
        response = client.post(f'/api/tournaments/{tid}/join', headers=player_headers)
        assert response.status_code == 409

    def test_join_full_tournament(self, client, player_headers):
        """Joining a full tournament returns 400."""
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Full', 'format': 'efl', 'max_participants': 1,
        })
        tid = create_resp.get_json()['tournament']['id']

        # Register and try joining
        reg = client.post('/api/auth/register', json={
            'email': 'full@test.com', 'password': 'testpass123', 'username': 'FullUser',
        })
        p2_headers = {'Authorization': f'Bearer {reg.get_json()["access_token"]}'}
        response = client.post(f'/api/tournaments/{tid}/join', headers=p2_headers)
        assert response.status_code == 400


class TestStartTournament:
    """Tests for POST /api/tournaments/<id>/start."""

    def _create_and_fill_tournament(self, client, creator_headers, num_players=4):
        """Helper: create tournament and add players."""
        create_resp = client.post('/api/tournaments', headers=creator_headers, json={
            'name': 'Start Test', 'format': 'efl', 'max_participants': num_players,
        })
        tid = create_resp.get_json()['tournament']['id']

        # Register additional players and join
        for i in range(2, num_players + 1):
            reg = client.post('/api/auth/register', json={
                'email': f'starter{i}@test.com',
                'password': 'testpass123',
                'username': f'Starter{i}',
            })
            token = reg.get_json()['access_token']
            client.post(f'/api/tournaments/{tid}/join',
                        headers={'Authorization': f'Bearer {token}'})

        return tid

    def test_start_success(self, client, player_headers):
        """Starting a tournament generates fixtures."""
        tid = self._create_and_fill_tournament(client, player_headers, num_players=4)

        response = client.post(f'/api/tournaments/{tid}/start', headers=player_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['match_count'] > 0
        assert data['tournament']['status'] == 'ongoing'

    def test_start_not_creator(self, client, player_headers):
        """Non-creator non-admin cannot start."""
        tid = self._create_and_fill_tournament(client, player_headers, num_players=3)

        # Login as a different non-admin player
        reg = client.post('/api/auth/register', json={
            'email': 'notcreator@test.com', 'password': 'testpass123', 'username': 'NotCreator',
        })
        other_headers = {'Authorization': f'Bearer {reg.get_json()["access_token"]}'}
        response = client.post(f'/api/tournaments/{tid}/start', headers=other_headers)
        assert response.status_code == 403

    def test_start_too_few_players(self, client, player_headers):
        """Starting with < 2 players fails."""
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Solo', 'format': 'efl', 'max_participants': 10,
        })
        tid = create_resp.get_json()['tournament']['id']

        response = client.post(f'/api/tournaments/{tid}/start', headers=player_headers)
        assert response.status_code == 400


class TestEFLFixtures:
    """Tests for EFL fixture generation (double round-robin)."""

    def test_efl_fixture_count(self, client, player_headers):
        """EFL with 4 players generates N*(N-1) = 12 matches."""
        # Create and fill
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'EFL Fixture Test', 'format': 'efl', 'max_participants': 4,
        })
        tid = create_resp.get_json()['tournament']['id']

        for i in range(2, 5):
            reg = client.post('/api/auth/register', json={
                'email': f'efl{i}@test.com', 'password': 'testpass123', 'username': f'EFL{i}',
            })
            token = reg.get_json()['access_token']
            client.post(f'/api/tournaments/{tid}/join',
                        headers={'Authorization': f'Bearer {token}'})

        # Start
        client.post(f'/api/tournaments/{tid}/start', headers=player_headers)

        # Check fixtures
        response = client.get(f'/api/tournaments/{tid}/matches')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_matches'] == 12  # 4 * 3 = 12 (double round-robin)


class TestStandings:
    """Tests for GET /api/tournaments/<id>/standings."""

    def test_standings_empty(self, client, player_headers):
        """Standings with no matches shows all players at 0."""
        create_resp = client.post('/api/tournaments', headers=player_headers, json={
            'name': 'Standings Test', 'format': 'efl', 'max_participants': 4,
        })
        tid = create_resp.get_json()['tournament']['id']

        response = client.get(f'/api/tournaments/{tid}/standings')
        assert response.status_code == 200
        standings = response.get_json()['standings']
        assert len(standings) >= 1
        assert standings[0]['pts'] == 0
