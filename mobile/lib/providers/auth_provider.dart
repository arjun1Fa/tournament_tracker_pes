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

  AuthState copyWith({User? user, bool? isLoading, String? error}) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error, // Can be null intentionally
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _apiClient;

  AuthNotifier(this._apiClient) : super(AuthState(isLoading: true)) {
    checkAuthStatus();
  }

  Future<void> checkAuthStatus() async {
    try {
      final response = await _apiClient.getMe();
      final user = User.fromJson(response.data['user']);
      state = AuthState(user: user, isLoading: false);
    } catch (e) {
      // If error (e.g. 401 or network), clear token and set unauthenticated
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

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthNotifier(apiClient);
});
