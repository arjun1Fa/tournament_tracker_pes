import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/tournament.dart';
import '../providers/auth_provider.dart';

final tournamentListProvider = FutureProvider.family<List<Tournament>, String?>((ref, status) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getTournaments(status: status);
  final data = response.data['tournaments'] as List;
  return data.map((e) => Tournament.fromJson(e)).toList();
});

final tournamentDetailProvider = FutureProvider.family<Tournament, int>((ref, id) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getTournament(id);
  return Tournament.fromJson(response.data['tournament']);
});

final createTournamentProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (Map<String, dynamic> data) async {
    final response = await apiClient.createTournament(data);
    ref.invalidate(tournamentListProvider); // Refresh list
    return Tournament.fromJson(response.data['tournament']);
  };
});

final joinTournamentProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (int id, {String? password}) async {
    await apiClient.joinTournament(id, password: password);
    ref.invalidate(tournamentDetailProvider(id)); // Refresh detail
  };
});

final startTournamentProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (int id) async {
    await apiClient.startTournament(id);
    ref.invalidate(tournamentDetailProvider(id)); // Refresh detail
  };
});
