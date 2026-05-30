import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/admin_provider.dart';

class AdminPanelScreen extends ConsumerStatefulWidget {
  const AdminPanelScreen({super.key});

  @override
  ConsumerState<AdminPanelScreen> createState() => _AdminPanelScreenState();
}

class _AdminPanelScreenState extends ConsumerState<AdminPanelScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Panel'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Users', icon: Icon(Icons.people)),
            Tab(text: 'Tournaments', icon: Icon(Icons.emoji_events)),
            Tab(text: 'Analytics', icon: Icon(Icons.analytics)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _UsersTab(),
          _TournamentsTab(),
          _AnalyticsTab(),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Users Tab
// ---------------------------------------------------------------------------
class _UsersTab extends ConsumerWidget {
  const _UsersTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final usersAsync = ref.watch(adminUsersProvider);

    return usersAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text('Error: $e')),
      data: (users) {
        if (users.isEmpty) return const Center(child: Text('No users found.'));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: users.length,
          itemBuilder: (ctx, i) {
            final user = users[i];
            final isSuspended = user['is_suspended'] == true;

            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: isSuspended ? Colors.red.shade100 : Colors.blue.shade100,
                  child: Text(
                    (user['username'] ?? '?')[0].toUpperCase(),
                    style: TextStyle(color: isSuspended ? Colors.red : Colors.blue),
                  ),
                ),
                title: Text(user['username'] ?? 'Unknown'),
                subtitle: Text(user['email'] ?? ''),
                trailing: isSuspended
                    ? TextButton(
                        onPressed: () => ref.read(adminSuspendUserProvider)(user['id'], false),
                        child: const Text('Unsuspend', style: TextStyle(color: Colors.green)),
                      )
                    : TextButton(
                        onPressed: () => ref.read(adminSuspendUserProvider)(user['id'], true),
                        child: const Text('Suspend', style: TextStyle(color: Colors.red)),
                      ),
              ),
            );
          },
        );
      },
    );
  }
}

// ---------------------------------------------------------------------------
// Tournaments Tab
// ---------------------------------------------------------------------------
class _TournamentsTab extends ConsumerWidget {
  const _TournamentsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tourneysAsync = ref.watch(adminTournamentsProvider);

    return tourneysAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text('Error: $e')),
      data: (tourneys) {
        if (tourneys.isEmpty) return const Center(child: Text('No tournaments.'));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: tourneys.length,
          itemBuilder: (ctx, i) {
            final t = tourneys[i];
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                title: Text(t['name'] ?? 'Untitled'),
                subtitle: Text('Status: ${t['status']} • Players: ${t['participant_count']}'),
                trailing: const Icon(Icons.chevron_right),
              ),
            );
          },
        );
      },
    );
  }
}

// ---------------------------------------------------------------------------
// Analytics Tab
// ---------------------------------------------------------------------------
class _AnalyticsTab extends ConsumerWidget {
  const _AnalyticsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(adminAnalyticsProvider);

    return analyticsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text('Error: $e')),
      data: (data) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              _AnalyticCard(
                icon: Icons.people,
                label: 'Total Users',
                value: '${data['total_users'] ?? 0}',
              ),
              _AnalyticCard(
                icon: Icons.emoji_events,
                label: 'Total Tournaments',
                value: '${data['total_tournaments'] ?? 0}',
              ),
              _AnalyticCard(
                icon: Icons.sports_soccer,
                label: 'Total Matches',
                value: '${data['total_matches'] ?? 0}',
              ),
              _AnalyticCard(
                icon: Icons.check_circle,
                label: 'Verified Matches',
                value: '${data['verified_matches'] ?? 0}',
              ),
              _AnalyticCard(
                icon: Icons.warning,
                label: 'Active Disputes',
                value: '${data['disputed_matches'] ?? 0}',
                valueColor: Colors.red,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _AnalyticCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _AnalyticCard({required this.icon, required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Icon(icon, size: 32, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 16),
            Expanded(child: Text(label, style: const TextStyle(fontSize: 16))),
            Text(
              value,
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: valueColor ?? Theme.of(context).colorScheme.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
