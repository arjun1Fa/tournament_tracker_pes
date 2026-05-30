import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../models/user.dart';
import '../core/network/api_client.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

class AuthState {
  final User? user;
  final bool isLoading;
  final String? error;

  AuthState({this.user, this.isLoading = false, this.error});

  bool get isAuthenticated => user != null;

  AuthState copyWith({User? user, bool? isLoading, String? error, bool clearUser = false}) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    // Check auth on initialization
    _checkAuthStatus();
    return AuthState(isLoading: true);
  }

  ApiClient get _apiClient => ref.read(apiClientProvider);

  Future<void> _checkAuthStatus() async {
    try {
      final response = await _apiClient.getMe();
      final user = User.fromJson(response.data['user']);
      state = AuthState(user: user, isLoading: false);
    } catch (e) {
      await _apiClient.clearToken();
      state = AuthState(isLoading: false);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.login(email, password);
      final token = response.data['access_token'];
      final user = User.fromJson(response.data['user']);

      await _apiClient.saveToken(token);
      state = AuthState(user: user, isLoading: false);
      return true;
    } on DioException catch (e) {
      final message = e.response?.data['error'] ?? 'Login failed. Check connection.';
      state = state.copyWith(isLoading: false, error: message);
      return false;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'An unexpected error occurred.');
      return false;
    }
  }

  Future<bool> register(String email, String username, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.register(email, username, password);
      final token = response.data['access_token'];
      final user = User.fromJson(response.data['user']);

      await _apiClient.saveToken(token);
      state = AuthState(user: user, isLoading: false);
      return true;
    } on DioException catch (e) {
      final message = e.response?.data['error'] ?? 'Registration failed.';
      state = state.copyWith(isLoading: false, error: message);
      return false;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'An unexpected error occurred.');
      return false;
    }
  }

  Future<void> logout() async {
    await _apiClient.clearToken();
    state = AuthState(isLoading: false);
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);
