import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sahurpay/features/sessions/session_repository.dart';
import 'package:sahurpay/features/sessions/session_list_screen.dart';
import 'package:sahurpay/features/sessions/session_detail_screen.dart';

void main() {
  testWidgets('shows the session list and summary', (tester) async {
    const repository = InMemorySessionRepository();
    await tester.pumpWidget(
      MaterialApp(
        home: SessionListScreen(
          sessions: repository.loadSessions(),
          onCreateSession: () async {},
        ),
      ),
    );

    expect(find.text('SahurPay'), findsOneWidget);
    expect(find.text('Payment history'), findsOneWidget);
    expect(find.text('All-time spend'), findsOneWidget);
    expect(find.text('Corner Market, Pharmacy'), findsOneWidget);
  });

  testWidgets('opens a session detail screen', (tester) async {
    const repository = InMemorySessionRepository();
    final session = repository.loadSessions().first;
    await tester.pumpWidget(
      MaterialApp(
        home: SessionDetailScreen(session: session),
      ),
    );

    expect(find.text('Session total'), findsOneWidget);
    expect(find.text('Stores'), findsOneWidget);
    expect(find.text('People'), findsOneWidget);
    expect(find.text('Corner Market'), findsOneWidget);
  });
}
