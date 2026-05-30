import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/tournament_provider.dart';
import '../../models/tournament.dart';

class TournamentListScreen extends ConsumerWidget {
  const TournamentListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // For the home screen, let's fetch all public tournaments (status: null gets all)
    final tournamentsAsync = ref.watch(tournamentListProvider(null));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tournaments'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // Future: Implement search
            },
          ),
        ],
      ),
      body: tournamentsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Failed to load tournaments\n$error', textAlign: TextAlign.center),
              TextButton(
                onPressed: () => ref.refresh(tournamentListProvider(null)),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (tournaments) {
          if (tournaments.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.emoji_events_outlined, size: 64, color: Colors.grey.shade400),
                  const SizedBox(height: 16),
                  Text(
                    'No tournaments yet',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.grey.shade600,
                        ),
                  ),
                  const SizedBox(height: 8),
                  const Text('Be the first to create one!'),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async => ref.refresh(tournamentListProvider(null)),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: tournaments.length,
              itemBuilder: (context, index) {
                return _TournamentCard(tournament: tournaments[index]);
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/tournaments/create'),
        icon: const Icon(Icons.add),
        label: const Text('Create'),
      ),
    );
  }
}

class _TournamentCard extends StatelessWidget {
  final Tournament tournament;

  const _TournamentCard({required this.tournament});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    // Status color
    Color statusColor;
    if (tournament.status == 'open') statusColor = theme.colorScheme.primary;
    else if (tournament.status == 'ongoing') statusColor = Colors.orange;
    else statusColor = Colors.grey;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/tournaments/${tournament.id}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      tournament.name,
                      style: theme.textTheme.titleLarge,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      tournament.status.toUpperCase(),
                      style: TextStyle(
                        color: statusColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.sports_esports, size: 16, color: theme.colorScheme.secondary),
                  const SizedBox(width: 4),
                  Text(
                    tournament.format.toUpperCase(),
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(width: 16),
                  Icon(Icons.people, size: 16, color: theme.colorScheme.secondary),
                  const SizedBox(width: 4),
                  Text(
                    '${tournament.participantCount}/${tournament.maxParticipants}',
                    style: theme.textTheme.bodyMedium,
                  ),
                  if (!tournament.isPublic) ...[
                    const Spacer(),
                    Icon(Icons.lock, size: 16, color: Colors.grey.shade500),
                  ]
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
