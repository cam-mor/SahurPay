import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'core/models/payment_models.dart';
import 'features/sessions/session_list_screen.dart';
import 'features/sessions/session_repository.dart';
import 'features/sessions/session_editor_screen.dart';

void main() {
  runApp(const SahurPayApp());
}

class SahurPayApp extends StatelessWidget {
  const SahurPayApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const _SahurPayBootstrap();
  }
}

class _SahurPayBootstrap extends StatefulWidget {
  const _SahurPayBootstrap();

  @override
  State<_SahurPayBootstrap> createState() => _SahurPayBootstrapState();
}

class _SahurPayBootstrapState extends State<_SahurPayBootstrap> {
  final SessionRepository _repository = SessionRepository();
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _repository.initialize().whenComplete(() {
      if (mounted) {
        setState(() {
          _initialized = true;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _repository,
      child: MaterialApp(
        title: 'SahurPay',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: ThemeMode.system,
        home: _initialized
            ? const _SahurPayHome()
            : const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              ),
      ),
    );
  }
}

class _SahurPayHome extends StatelessWidget {
  const _SahurPayHome();

  @override
  Widget build(BuildContext context) {
    return Consumer<SessionRepository>(
      builder: (context, repository, _) {
        return SessionListScreen(
          sessions: repository.sessions,
          onCreateSession: () async {
            final session = await Navigator.of(context).push<PaymentSession>(
              MaterialPageRoute(
                builder: (_) => const SessionEditorScreen(),
              ),
            );
            if (session != null) {
              await repository.addSession(session);
            }
          },
        );
      },
    );
  }
}
