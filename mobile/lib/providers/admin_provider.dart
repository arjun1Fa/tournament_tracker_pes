import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';

final adminUsersProvider = FutureProvider.autoDispose((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getAdminUsers();
  return response.data['users'] as List;
});

final adminTournamentsProvider = FutureProvider.autoDispose((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getAdminTournaments();
  return response.data['tournaments'] as List;
});

final adminAnalyticsProvider = FutureProvider.autoDispose((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getAdminAnalytics();
  return response.data;
});

final adminSuspendUserProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (int userId, bool suspended) async {
    await apiClient.suspendUser(userId, suspended);
    ref.invalidate(adminUsersProvider);
  };
});

final adminResolveDisputeProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (int matchId, Map<String, dynamic> resolutionData) async {
    await apiClient.resolveDispute(matchId, resolutionData);
    // Invalidate globally or wherever needed
  };
});
