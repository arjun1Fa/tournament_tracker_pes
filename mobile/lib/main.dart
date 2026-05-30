import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'screens/home_screen.dart';
import 'screens/tournament_detail_screen.dart';
import 'screens/match_detail_screen.dart';
import 'screens/admin_login_screen.dart';
import 'screens/admin_dashboard_screen.dart';
import 'screens/admin_tournament_manage_screen.dart';
import 'screens/admin_match_input_screen.dart';

void main() {
  runApp(const ProviderScope(child: MyApp()));
}

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/tournaments/:id',
      builder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return TournamentDetailScreen(tournamentId: id);
      },
    ),
    GoRoute(
      path: '/matches/:id',
      builder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return MatchDetailScreen(matchId: id);
      },
    ),
    GoRoute(
      path: '/admin/login',
      builder: (context, state) => const AdminLoginScreen(),
    ),
    GoRoute(
      path: '/admin/dashboard',
      builder: (context, state) => const AdminDashboardScreen(),
    ),
    GoRoute(
      path: '/admin/tournaments/:id',
      builder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return AdminTournamentManageScreen(tournamentId: id);
      },
    ),
    GoRoute(
      path: '/admin/matches/:id',
      builder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return AdminMatchInputScreen(matchId: id);
      },
    ),
  ],
);

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'eFootball Tournament Tracker',
      theme: ThemeData.dark().copyWith(
        primaryColor: const Color(0xFF6200EE),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFBB86FC),
          secondary: Color(0xFF03DAC6),
          surface: Color(0xFF1E1E1E),
          background: Color(0xFF121212),
        ),
        scaffoldBackgroundColor: const Color(0xFF121212),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1E1E1E),
          elevation: 0,
        ),
        cardTheme: CardTheme(
          color: const Color(0xFF1E1E1E),
          elevation: 4,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      routerConfig: _router,
    );
  }
}
