import 'package:flutter/material.dart';

import 'core/theme/app_theme.dart';
import 'features/sessions/session_list_screen.dart';
import 'features/sessions/session_repository.dart';

void main() {
  runApp(const SahurPayApp());
}

class SahurPayApp extends StatelessWidget {
  const SahurPayApp({super.key});

  @override
  Widget build(BuildContext context) {
    const repository = InMemorySessionRepository();
    return MaterialApp(
      title: 'SahurPay',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      home: SessionListScreen(
        sessions: repository.loadSessions(),
      ),
    );
  }
}
