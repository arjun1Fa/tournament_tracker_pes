import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';

// Since standings is deeply tied to the tournament but has complex shape, 
// we will fetch it directly here with a FutureProvider.
final standingsProvider = FutureProvider.family<Map<String, dynamic>, int>((ref, tournamentId) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getStandings(tournamentId);
  return response.data;
});

class StandingsScreen extends ConsumerWidget {
  final int tournamentId;

  const StandingsScreen({super.key, required this.tournamentId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final standingsAsync = ref.watch(standingsProvider(tournamentId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('League Standings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(standingsProvider(tournamentId)),
          ),
        ],
      ),
      body: standingsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
        data: (data) {
          final standings = data['standings'] as List;
          if (standings.isEmpty) {
            return const Center(child: Text('No standings available yet.'));
          }

          return SingleChildScrollView(
            scrollDirection: Axis.vertical,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingTextStyle: const TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
                columns: const [
                  DataColumn(label: Text('#')),
                  DataColumn(label: Text('Player')),
                  DataColumn(label: Text('MP')), // Matches Played
                  DataColumn(label: Text('W')),
                  DataColumn(label: Text('D')),
                  DataColumn(label: Text('L')),
                  DataColumn(label: Text('GF')),
                  DataColumn(label: Text('GA')),
                  DataColumn(label: Text('GD')),
                  DataColumn(label: Text('Pts', style: TextStyle(color: Colors.green))),
                ],
                rows: List.generate(standings.length, (index) {
                  final row = standings[index];
                  return DataRow(
                    cells: [
                      DataCell(Text('${index + 1}')),
                      DataCell(Text(row['username'] ?? 'TBD', style: const TextStyle(fontWeight: FontWeight.w600))),
                      DataCell(Text('${row['played']}')),
                      DataCell(Text('${row['wins']}')),
                      DataCell(Text('${row['draws']}')),
                      DataCell(Text('${row['losses']}')),
                      DataCell(Text('${row['goals_for']}')),
                      DataCell(Text('${row['goals_against']}')),
                      DataCell(Text('${row['goal_difference']}')),
                      DataCell(Text('${row['points']}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green))),
                    ],
                  );
                }),
              ),
            ),
          );
        },
      ),
    );
  }
}
