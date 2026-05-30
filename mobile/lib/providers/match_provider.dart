import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/match.dart';
import '../providers/auth_provider.dart';

final matchDetailProvider = FutureProvider.family<Match, int>((ref, id) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getMatch(id);
  return Match.fromJson(response.data['match']);
});

final tournamentMatchesProvider = FutureProvider.family<List<Match>, int>((ref, tournamentId) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getMatches(tournamentId);
  final data = response.data['matches'] as List;
  return data.map((e) => Match.fromJson(e)).toList();
});

final reportMatchProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (int id, Map<String, dynamic> data) async {
    final response = await apiClient.reportMatch(id, data);
    ref.invalidate(matchDetailProvider(id));
    return response.data;
  };
});

final verifyMatchProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return (int id, String myTeam, bool confirmed) async {
    final response = await apiClient.verifyMatch(id, myTeam, confirmed);
    ref.invalidate(matchDetailProvider(id));
    return response.data;
  };
});
