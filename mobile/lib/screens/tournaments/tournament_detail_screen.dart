import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/tournament_provider.dart';
import '../../providers/auth_provider.dart';
import '../../models/tournament.dart';

class TournamentDetailScreen extends ConsumerStatefulWidget {
  final int tournamentId;

  const TournamentDetailScreen({super.key, required this.tournamentId});

  @override
  ConsumerState<TournamentDetailScreen> createState() => _TournamentDetailScreenState();
}

class _TournamentDetailScreenState extends ConsumerState<TournamentDetailScreen> {
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _joinTournament(Tournament tournament) async {
    final joinFn = ref.read(joinTournamentProvider);
    try {
      if (tournament.hasPassword) {
        bool? joined = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('Private Tournament'),
            content: TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: 'Password'),
              obscureText: true,
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
              ElevatedButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Join'),
              ),
            ],
          ),
        );
        if (joined != true) return;
      }
      
      await joinFn(tournament.id, password: _passwordController.text.isNotEmpty ? _passwordController.text : null);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Joined successfully!')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to join: $e')));
      }
    }
  }

  Future<void> _startTournament(Tournament tournament) async {
    try {
      final startFn = ref.read(startTournamentProvider);
      await startFn(tournament.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Tournament started!')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to start: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncData = ref.watch(tournamentDetailProvider(widget.tournamentId));
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tournament Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(tournamentDetailProvider(widget.tournamentId)),
          ),
        ],
      ),
      body: asyncData.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
        data: (tournament) {
          final isParticipant = tournament.participants?.any((p) => p.userId == user?.id) ?? false;
          final isAdmin = user?.isAdmin == true;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        const Icon(Icons.emoji_events, size: 64, color: Colors.amber),
                        const SizedBox(height: 16),
                        Text(
                          tournament.name,
                          style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 24),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${tournament.status.toUpperCase()} • ${tournament.format.toUpperCase()}',
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: Theme.of(context).colorScheme.primary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.people, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              '${tournament.participantCount} / ${tournament.maxParticipants} Players',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 24),
                
                // Actions
                if (tournament.status == 'open' && !isParticipant)
                  ElevatedButton(
                    onPressed: () => _joinTournament(tournament),
                    child: const Text('Join Tournament'),
                  ),
                  
                if (isAdmin && tournament.status == 'open' && tournament.participantCount > 1)
                  Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
                      onPressed: () => _startTournament(tournament),
                      child: const Text('Start Tournament (Admin)'),
                    ),
                  ),

                const SizedBox(height: 32),
                
                // Participants List
                Text(
                  'Participants',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                if (tournament.participants == null || tournament.participants!.isEmpty)
                  const Text('No players joined yet.')
                else
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: tournament.participants!.length,
                    itemBuilder: (ctx, i) {
                      final p = tournament.participants![i];
                      return ListTile(
                        leading: CircleAvatar(child: Text(p.user?.username[0].toUpperCase() ?? '?')),
                        title: Text(p.user?.username ?? 'Unknown Player'),
                        subtitle: p.seed != null ? Text('Seed: ${p.seed}') : null,
                      );
                    },
                  ),
                // Matches List
                const SizedBox(height: 32),
                Text(
                  'Tournament Matches',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                _TournamentMatchesList(tournamentId: tournament.id),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _TournamentMatchesList extends ConsumerWidget {
  final int tournamentId;

  const _TournamentMatchesList({required this.tournamentId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final matchesAsync = ref.watch(tournamentMatchesProvider(tournamentId));
    
    return matchesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Text('Error loading matches: $e'),
      data: (matches) {
        if (matches.isEmpty) return const Text('No matches scheduled yet.');
        
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: matches.length,
          itemBuilder: (ctx, i) {
            final match = matches[i];
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                onTap: () => context.push('/matches/${match.id}'),
                title: Text('${match.team1Name ?? match.player1?.username ?? 'TBD'} vs ${match.team2Name ?? match.player2?.username ?? 'TBD'}'),
                subtitle: Text('${match.round} • Status: ${match.status}'),
                trailing: const Icon(Icons.chevron_right),
              ),
            );
          },
        );
      },
    );
  }
}
