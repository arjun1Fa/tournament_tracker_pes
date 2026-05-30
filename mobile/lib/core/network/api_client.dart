import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  late final Dio dio;
  final _storage = const FlutterSecureStorage();
  final String _baseUrl = 'https://efootball-tracker.onrender.com/api';

  ApiClient() {
    dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'admin_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (e, handler) async {
        if (e.response?.statusCode == 401) {
          await _storage.delete(key: 'admin_token');
        }
        return handler.next(e);
      },
    ));
  }

  // --- Admin Auth ---
  Future<Response> login(String username, String password) {
    return dio.post('/auth/login', data: {
      'username': username,
      'password': password,
    });
  }

  Future<void> saveToken(String token) async {
    await _storage.write(key: 'admin_token', value: token);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: 'admin_token');
  }

  Future<bool> hasToken() async {
    final token = await _storage.read(key: 'admin_token');
    return token != null;
  }

  // --- Public Read ---
  Future<Response> getTournaments() {
    return dio.get('/tournaments');
  }

  Future<Response> getTournament(int id) {
    return dio.get('/tournaments/$id');
  }

  Future<Response> getMatches(int tournamentId) {
    return dio.get('/tournaments/$tournamentId/matches');
  }

  Future<Response> getStandings(int tournamentId) {
    return dio.get('/tournaments/$tournamentId/standings');
  }

  Future<Response> getLeaderboard(int tournamentId) {
    return dio.get('/tournaments/$tournamentId/leaderboard');
  }

  Future<Response> getMatch(int matchId) {
    return dio.get('/matches/$matchId');
  }

  // --- Admin Writes ---
  Future<Response> createTournament(String name) {
    return dio.post('/admin/tournaments', data: {'name': name});
  }

  Future<Response> deleteTournament(int id) {
    return dio.delete('/admin/tournaments/$id');
  }

  Future<Response> addPlayer(int tournamentId, Map<String, dynamic> data) {
    return dio.post('/admin/tournaments/$tournamentId/players', data: data);
  }

  Future<Response> updatePlayer(int playerId, Map<String, dynamic> data) {
    return dio.patch('/admin/players/$playerId', data: data);
  }

  Future<Response> deletePlayer(int playerId) {
    return dio.delete('/admin/players/$playerId');
  }

  Future<Response> startTournament(int id) {
    return dio.post('/admin/tournaments/$id/start');
  }

  Future<Response> startPlayoffs(int id) {
    return dio.post('/admin/tournaments/$id/start_playoffs');
  }

  Future<Response> updateMatch(int matchId, Map<String, dynamic> data) {
    return dio.patch('/admin/matches/$matchId', data: data);
  }
}
