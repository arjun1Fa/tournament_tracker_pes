import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme.dart';
import 'core/router.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // We wrap the entire app in ProviderScope so Riverpod can manage state
  runApp(const ProviderScope(child: EFootballTrackerApp()));
}

class EFootballTrackerApp extends ConsumerWidget {
  const EFootballTrackerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'eFootball Tracker',
      theme: AppTheme.lightTheme, // Simple and humane theme
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
