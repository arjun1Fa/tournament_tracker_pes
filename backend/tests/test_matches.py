"""Tests for match routes — report and verify flow."""


class TestMatchReport:
    """Tests for POST /api/matches/<id>/report."""

    def _setup_tournament_with_match(self, client):
        """Helper: create tournament with 2 players, start it, return match ID and headers."""
        # Register player 1
        reg1 = client.post('/api/auth/register', json={
            'email': 'reporter@test.com', 'password': 'testpass123', 'username': 'Reporter',
        })
        p1_token = reg1.get_json()['access_token']
        p1_headers = {'Authorization': f'Bearer {p1_token}'}

        # Create tournament
        create_resp = client.post('/api/tournaments', headers=p1_headers, json={
            'name': 'Match Test', 'format': 'round_robin', 'max_participants': 2,
        })
        tid = create_resp.get_json()['tournament']['id']

        # Register player 2
        reg2 = client.post('/api/auth/register', json={
            'email': 'verifier@test.com', 'password': 'testpass123', 'username': 'Verifier',
        })
        p2_token = reg2.get_json()['access_token']
        p2_headers = {'Authorization': f'Bearer {p2_token}'}

        # Player 2 joins
        client.post(f'/api/tournaments/{tid}/join', headers=p2_headers)

        # Start tournament
        client.post(f'/api/tournaments/{tid}/start', headers=p1_headers)

        # Get first match
        matches_resp = client.get(f'/api/tournaments/{tid}/matches')
        rounds = matches_resp.get_json()['rounds']
        first_round = list(rounds.values())[0]
        match_id = first_round[0]['id']

        return match_id, p1_headers, p2_headers

    def _sample_report_data(self):
        """Sample OCR-extracted match data."""
        return {
            'team1_name': 'joshua',
            'team2_name': 'La Remontada',
            'score1': 2,
            'score2': 4,
            'my_team': 'team1',
            'team1_stats': {
                'possession': 51.0,
                'shots': 3,
                'shots_on_target': 2,
                'fouls': 1,
                'offsides': 0,
                'corner_kicks': 0,
                'free_kicks': 1,
                'passes': 76,
                'successful_passes': 57,
                'crosses': 2,
                'interceptions': 11,
                'tackles': 4,
                'saves': 1,
            },
            'team2_stats': {
                'possession': 49.0,
                'shots': 11,
                'shots_on_target': 10,
                'fouls': 1,
                'offsides': 1,
                'corner_kicks': 1,
                'free_kicks': 1,
                'passes': 63,
                'successful_passes': 47,
                'crosses': 0,
                'interceptions': 18,
                'tackles': 10,
                'saves': 0,
            },
        }

    def test_report_match_success(self, client, db):
        """Successfully report a match result."""
        match_id, p1_headers, _ = self._setup_tournament_with_match(client)

        response = client.post(
            f'/api/matches/{match_id}/report',
            headers=p1_headers,
            json=self._sample_report_data(),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'Waiting for opponent' in data['message']

        # Verify match status is pending
        match_resp = client.get(f'/api/matches/{match_id}')
        assert match_resp.get_json()['match']['status'] == 'pending_verification'

    def test_report_match_not_participant(self, client, db):
        """Non-participant cannot report."""
        match_id, _, _ = self._setup_tournament_with_match(client)

        # Register a third player (not in tournament)
        reg3 = client.post('/api/auth/register', json={
            'email': 'outsider@test.com', 'password': 'testpass123', 'username': 'Outsider',
        })
        outsider_headers = {'Authorization': f'Bearer {reg3.get_json()["access_token"]}'}

        response = client.post(
            f'/api/matches/{match_id}/report',
            headers=outsider_headers,
            json=self._sample_report_data(),
        )
        assert response.status_code == 403

    def test_report_match_missing_data(self, client, db):
        """Incomplete data returns 400."""
        match_id, p1_headers, _ = self._setup_tournament_with_match(client)

        response = client.post(
            f'/api/matches/{match_id}/report',
            headers=p1_headers,
            json={'team1_name': 'only one field'},
        )
        assert response.status_code == 400


class TestMatchVerify:
    """Tests for POST /api/matches/<id>/verify."""

    def _setup_reported_match(self, client):
        """Helper: create tournament, start, report a match. Return IDs and headers."""
        reg1 = client.post('/api/auth/register', json={
            'email': 'vrep@test.com', 'password': 'testpass123', 'username': 'VReporter',
        })
        p1_token = reg1.get_json()['access_token']
        p1_headers = {'Authorization': f'Bearer {p1_token}'}

        create_resp = client.post('/api/tournaments', headers=p1_headers, json={
            'name': 'Verify Test', 'format': 'round_robin', 'max_participants': 2,
        })
        tid = create_resp.get_json()['tournament']['id']

        reg2 = client.post('/api/auth/register', json={
            'email': 'vver@test.com', 'password': 'testpass123', 'username': 'VVerifier',
        })
        p2_token = reg2.get_json()['access_token']
        p2_headers = {'Authorization': f'Bearer {p2_token}'}

        client.post(f'/api/tournaments/{tid}/join', headers=p2_headers)
        client.post(f'/api/tournaments/{tid}/start', headers=p1_headers)

        matches_resp = client.get(f'/api/tournaments/{tid}/matches')
        rounds = matches_resp.get_json()['rounds']
        first_round = list(rounds.values())[0]
        match_id = first_round[0]['id']

        # Report
        client.post(f'/api/matches/{match_id}/report', headers=p1_headers, json={
            'team1_name': 'TeamA', 'team2_name': 'TeamB',
            'score1': 3, 'score2': 1, 'my_team': 'team1',
            'team1_stats': {'possession': 60, 'shots': 8, 'shots_on_target': 5,
                            'fouls': 2, 'offsides': 1, 'corner_kicks': 3,
                            'free_kicks': 2, 'passes': 200, 'successful_passes': 170,
                            'crosses': 5, 'interceptions': 12, 'tackles': 8, 'saves': 2},
            'team2_stats': {'possession': 40, 'shots': 4, 'shots_on_target': 2,
                            'fouls': 3, 'offsides': 0, 'corner_kicks': 1,
                            'free_kicks': 3, 'passes': 150, 'successful_passes': 110,
                            'crosses': 2, 'interceptions': 8, 'tackles': 5, 'saves': 4},
        })

        return match_id, tid, p1_headers, p2_headers

    def test_verify_confirm(self, client, db):
        """Opponent confirms → match becomes verified."""
        match_id, _, _, p2_headers = self._setup_reported_match(client)

        response = client.post(f'/api/matches/{match_id}/verify', headers=p2_headers, json={
            'my_team': 'team2',
            'confirmed': True,
        })
        assert response.status_code == 200
        assert 'verified' in response.get_json()['message'].lower()

        # Check match status
        match_resp = client.get(f'/api/matches/{match_id}')
        assert match_resp.get_json()['match']['status'] == 'verified'

    def test_verify_dispute(self, client, db):
        """Opponent disputes → match becomes disputed."""
        match_id, _, _, p2_headers = self._setup_reported_match(client)

        response = client.post(f'/api/matches/{match_id}/verify', headers=p2_headers, json={
            'confirmed': False,
        })
        assert response.status_code == 200
        assert 'disputed' in response.get_json()['message'].lower()

    def test_reporter_cannot_verify_own(self, client, db):
        """Reporter cannot verify their own report."""
        match_id, _, p1_headers, _ = self._setup_reported_match(client)

        response = client.post(f'/api/matches/{match_id}/verify', headers=p1_headers, json={
            'my_team': 'team1', 'confirmed': True,
        })
        assert response.status_code == 400

    def test_standings_update_after_verify(self, client, db):
        """Standings reflect verified match results."""
        match_id, tid, _, p2_headers = self._setup_reported_match(client)

        # Verify
        client.post(f'/api/matches/{match_id}/verify', headers=p2_headers, json={
            'my_team': 'team2', 'confirmed': True,
        })

        # Check standings
        standings_resp = client.get(f'/api/tournaments/{tid}/standings')
        standings = standings_resp.get_json()['standings']
        assert len(standings) == 2

        # Winner should be ranked #1 with 3 points
        winner = standings[0]
        assert winner['pts'] == 3
        assert winner['w'] == 1
        assert winner['gf'] == 3
        assert winner['ga'] == 1


class TestMatchExport:
    """Tests for GET /api/matches/<id>/export."""

    def test_export_unverified_fails(self, client, db):
        """Cannot export unverified match."""
        # Quick setup: just need a scheduled match
        reg = client.post('/api/auth/register', json={
            'email': 'exp1@test.com', 'password': 'testpass123', 'username': 'Exp1',
        })
        p1_headers = {'Authorization': f'Bearer {reg.get_json()["access_token"]}'}

        create_resp = client.post('/api/tournaments', headers=p1_headers, json={
            'name': 'Export Test', 'format': 'round_robin', 'max_participants': 2,
        })
        tid = create_resp.get_json()['tournament']['id']

        reg2 = client.post('/api/auth/register', json={
            'email': 'exp2@test.com', 'password': 'testpass123', 'username': 'Exp2',
        })
        p2_headers = {'Authorization': f'Bearer {reg2.get_json()["access_token"]}'}
        client.post(f'/api/tournaments/{tid}/join', headers=p2_headers)
        client.post(f'/api/tournaments/{tid}/start', headers=p1_headers)

        matches_resp = client.get(f'/api/tournaments/{tid}/matches')
        rounds = matches_resp.get_json()['rounds']
        match_id = list(rounds.values())[0][0]['id']

        response = client.get(f'/api/matches/{match_id}/export')
        assert response.status_code == 400
