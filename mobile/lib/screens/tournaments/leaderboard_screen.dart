import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';

final leaderboardProvider = FutureProvider.family<Map<String, dynamic>, int>((ref, tournamentId) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getLeaderboard(tournamentId);
  return response.data;
});

class LeaderboardScreen extends ConsumerWidget {
  final int tournamentId;

  const LeaderboardScreen({super.key, required this.tournamentId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final leaderAsync = ref.watch(leaderboardProvider(tournamentId));

    return Scaffold(
      appBar: AppBar(title: const Text('Leaderboard & MVP')),
      body: leaderAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
        data: (data) {
          final mvp = data['mvp_rankings'] as List? ?? [];
          final statLeaders = data['stat_leaders'] as Map<String, dynamic>? ?? {};

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // MVP Rankings
                Text('MVP Rankings', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                if (mvp.isEmpty)
                  const Text('No MVP data yet.')
                else
                  ...mvp.asMap().entries.map((entry) {
                    final i = entry.key;
                    final player = entry.value;
                    final isTop3 = i < 3;
                    return Card(
                      color: isTop3 ? Theme.of(context).colorScheme.primary.withValues(alpha: 0.05) : null,
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: isTop3 ? Colors.amber : Colors.grey.shade300,
                          child: Text('${i + 1}', style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: isTop3 ? Colors.white : Colors.black87,
                          )),
                        ),
                        title: Text(
                          player['username'] ?? 'Unknown',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        trailing: Text(
                          '${player['mvp_score']?.toStringAsFixed(1) ?? '0'} pts',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.primary,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    );
                  }),

                const SizedBox(height: 32),

                // Stat Leaders
                Text('Stat Leaders', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                if (statLeaders.isEmpty)
                  const Text('No stats recorded yet.')
                else
                  ...statLeaders.entries.map((entry) {
                    final statName = entry.key.replaceAll('_', ' ');
                    final leaders = entry.value as List? ?? [];
                    if (leaders.isEmpty) return const SizedBox.shrink();
                    final top = leaders.first;
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        title: Text(_formatStatName(statName)),
                        subtitle: Text(top['username'] ?? 'Unknown'),
                        trailing: Text(
                          '${top['value']}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                        ),
                      ),
                    );
                  }),
              ],
            ),
          );
        },
      ),
    );
  }

  String _formatStatName(String name) {
    return name.split(' ').map((w) => w[0].toUpperCase() + w.substring(1)).join(' ');
  }
}
