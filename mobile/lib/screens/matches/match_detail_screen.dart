import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/match_provider.dart';
import '../../providers/auth_provider.dart';
import '../../models/match.dart' as m;

class MatchDetailScreen extends ConsumerWidget {
  final int matchId;

  const MatchDetailScreen({super.key, required this.matchId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final matchAsync = ref.watch(matchDetailProvider(matchId));
    final currentUser = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Match Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(matchDetailProvider(matchId)),
          ),
        ],
      ),
      body: matchAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
        data: (match) {
          final isPlayer1 = match.player1Id == currentUser?.id;
          final isPlayer2 = match.player2Id == currentUser?.id;
          final isParticipant = isPlayer1 || isPlayer2;
          
          final needsMyVerification = 
              (isPlayer1 && !match.verifiedByPlayer1 && match.status == 'pending_verification') ||
              (isPlayer2 && !match.verifiedByPlayer2 && match.status == 'pending_verification');

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Scoreboard Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        Text(match.round.toUpperCase(), style: Theme.of(context).textTheme.bodySmall?.copyWith(letterSpacing: 1.2)),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            // Player 1
                            Expanded(
                              child: Column(
                                children: [
                                  CircleAvatar(radius: 24, child: Text(match.player1?.username[0].toUpperCase() ?? '?')),
                                  const SizedBox(height: 8),
                                  Text(match.player1?.username ?? 'TBD', textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold)),
                                  Text(match.team1Name ?? 'Selects Team', style: Theme.of(context).textTheme.bodySmall),
                                ],
                              ),
                            ),
                            
                            // Score
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                              child: Text(
                                match.score1 != null && match.score2 != null 
                                    ? '${match.score1} - ${match.score2}' 
                                    : 'VS',
                                style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 40),
                              ),
                            ),
                            
                            // Player 2
                            Expanded(
                              child: Column(
                                children: [
                                  CircleAvatar(radius: 24, child: Text(match.player2?.username[0].toUpperCase() ?? '?')),
                                  const SizedBox(height: 8),
                                  Text(match.player2?.username ?? 'TBD', textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold)),
                                  Text(match.team2Name ?? 'Selects Team', style: Theme.of(context).textTheme.bodySmall),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _StatusBadge(status: match.status),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 24),

                // Action Buttons
                if (isParticipant && match.status == 'scheduled')
                  ElevatedButton.icon(
                    onPressed: () => context.push('/matches/${match.id}/report'),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Report Match Result'),
                  ),
                  
                if (needsMyVerification)
                  Card(
                    color: Colors.orange.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          const Text('Your opponent reported the result. Please verify it.'),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
                                  onPressed: () async {
                                    final myTeam = isPlayer1 ? 'team1' : 'team2';
                                    await ref.read(verifyMatchProvider)(match.id, myTeam, false);
                                  },
                                  child: const Text('Dispute'),
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: ElevatedButton(
                                  style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                  onPressed: () async {
                                    final myTeam = isPlayer1 ? 'team1' : 'team2';
                                    await ref.read(verifyMatchProvider)(match.id, myTeam, true);
                                  },
                                  child: const Text('Confirm'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                // Stats Section
                if (match.stats != null && match.stats!.isNotEmpty) ...[
                  const SizedBox(height: 32),
                  Text('Match Statistics', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 16),
                  _buildStatRow('Possession', match, (s) => '${s.possession?.toStringAsFixed(0)}%'),
                  _buildStatRow('Shots', match, (s) => s.shots.toString()),
                  _buildStatRow('On Target', match, (s) => s.shotsOnTarget.toString()),
                  _buildStatRow('Passes', match, (s) => s.passes.toString()),
                  _buildStatRow('Fouls', match, (s) => s.fouls.toString()),
                ]
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatRow(String label, m.Match match, String Function(m.MatchStats) selector) {
    if (match.stats == null || match.stats!.length < 2) return const SizedBox.shrink();
    // Assuming stats[0] is team1 and stats[1] is team2 (or vice versa, match models handle this)
    final s1 = match.stats!.firstWhere((s) => s.userId == match.player1Id, orElse: () => match.stats![0]);
    final s2 = match.stats!.firstWhere((s) => s.userId == match.player2Id, orElse: () => match.stats![1]);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(child: Text(selector(s1), textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold))),
          Expanded(child: Text(label, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey))),
          Expanded(child: Text(selector(s2), textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold))),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    if (status == 'verified') color = Colors.green;
    else if (status == 'pending_verification') color = Colors.orange;
    else if (status == 'disputed') color = Colors.red;
    else color = Colors.grey;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        status.toUpperCase().replaceAll('_', ' '),
        style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }
}
