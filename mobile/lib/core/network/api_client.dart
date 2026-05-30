import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:io';
import 'package:flutter/foundation.dart';

class ApiClient {
  static const String _baseUrlLocalAndroid = 'http://10.0.2.2:5000/api';
  static const String _baseUrlLocalIOS = 'http://127.0.0.1:5000/api';
  // TODO: Update with Render URL once deployed
  static const String _baseUrlProd = 'https://efootball-tracker-api.onrender.com/api';

  final Dio dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient() : dio = Dio() {
    dio.options.baseUrl = _getBaseUrl();
    dio.options.connectTimeout = const Duration(seconds: 10);
    dio.options.receiveTimeout = const Duration(seconds: 10);

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Inject JWT token into headers if available
        final token = await _storage.read(key: 'jwt_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) async {
        // Handle 401 Unauthorized (token expiry)
        if (e.response?.statusCode == 401) {
          // Future: Implement automatic token refresh here if a refresh token exists
          await _storage.delete(key: 'jwt_token');
        }
        return handler.next(e);
      },
    ));
  }

  String _getBaseUrl() {
    // Production Render URL
    return 'https://efootball-tracker.onrender.com/api';
  }

  // --- Auth API ---
  Future<Response> register(String email, String username, String password) {
    return dio.post('/auth/register', data: {
      'email': email,
      'username': username,
      'password': password,
    });
  }

  Future<Response> login(String login, String password) {
    return dio.post('/auth/login', data: {
      'login': login,
      'password': password,
    });
  }

  Future<Response> getMe() {
    return dio.get('/auth/me');
  }

  // --- Tournament API ---
  Future<Response> getTournaments({String? status}) {
    final query = status != null ? {'status': status} : null;
    return dio.get('/tournaments', queryParameters: query);
  }

  Future<Response> getTournament(int id) {
    return dio.get('/tournaments/$id');
  }

  Future<Response> createTournament(Map<String, dynamic> data) {
    return dio.post('/tournaments', data: data);
  }

  Future<Response> joinTournament(int id, {String? password}) {
    return dio.post('/tournaments/$id/join', data: {
      if (password != null) 'password': password,
    });
  }

  Future<Response> startTournament(int id) {
    return dio.post('/tournaments/$id/start');
  }

  Future<Response> getMatches(int id) {
    return dio.get('/tournaments/$id/matches');
  }

  Future<Response> getStandings(int id) {
    return dio.get('/tournaments/$id/standings');
  }

  Future<Response> getLeaderboard(int id) {
    return dio.get('/tournaments/$id/leaderboard');
  }

  // --- Match API ---
  Future<Response> getMatch(int id) {
    return dio.get('/matches/$id');
  }

  Future<Response> reportMatch(int id, Map<String, dynamic> data) {
    return dio.post('/matches/$id/report', data: data);
  }

  Future<Response> verifyMatch(int id, String myTeam, bool confirmed) {
    return dio.post('/matches/$id/verify', data: {
      'my_team': myTeam,
      'confirmed': confirmed,
    });
  }

  // --- Admin API ---
  Future<Response> getAdminUsers() {
    return dio.get('/admin/users');
  }

  Future<Response> suspendUser(int userId, bool suspended) {
    return dio.post('/admin/users/$userId/suspend', data: {'suspended': suspended});
  }

  Future<Response> getAdminTournaments() {
    return dio.get('/admin/tournaments');
  }

  Future<Response> resolveDispute(int matchId, Map<String, dynamic> data) {
    return dio.post('/admin/disputes/$matchId/resolve', data: data);
  }

  Future<Response> getAdminAnalytics() {
    return dio.get('/admin/analytics');
  }

  // Tokens
  Future<void> saveToken(String token) async {
    await _storage.write(key: 'jwt_token', value: token);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: 'jwt_token');
  }
}
