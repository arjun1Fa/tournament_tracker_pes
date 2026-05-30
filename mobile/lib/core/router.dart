import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/auth_provider.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/tournaments/create_tournament_screen.dart';
import '../screens/tournaments/tournament_detail_screen.dart';
import '../screens/tournaments/standings_screen.dart';
import '../screens/tournaments/leaderboard_screen.dart';
import '../screens/matches/match_detail_screen.dart';
import '../screens/matches/report_match_screen.dart';
import '../screens/admin/admin_panel_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      // If we are still checking auth status on startup, show loading
      if (authState.isLoading && !authState.isAuthenticated) {
        return null; // Will show a loading screen if we define one, or stay put
      }

      final isGoingToAuth = state.matchedLocation == '/login' || state.matchedLocation == '/register';

      // Not authenticated and trying to access private page -> redirect to login
      if (!authState.isAuthenticated && !isGoingToAuth) {
        return '/login';
      }

      // Authenticated but trying to access auth pages -> redirect to home
      if (authState.isAuthenticated && isGoingToAuth) {
        return '/';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/',
        builder: (context, state) {
          // If still loading on initial launch, show a spinner
          if (authState.isLoading) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          return const HomeScreen();
        },
      ),
      GoRoute(
        path: '/tournaments/create',
        builder: (context, state) => const CreateTournamentScreen(),
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
        path: '/matches/:id/report',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return ReportMatchScreen(matchId: id);
        },
      ),
      GoRoute(
        path: '/tournaments/:id/standings',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return StandingsScreen(tournamentId: id);
        },
      ),
      GoRoute(
        path: '/tournaments/:id/leaderboard',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return LeaderboardScreen(tournamentId: id);
        },
      ),
      GoRoute(
        path: '/admin',
        builder: (context, state) => const AdminPanelScreen(),
      ),
    ],
  );
});
