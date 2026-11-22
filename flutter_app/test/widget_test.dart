import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:sahurpay/features/sessions/session_repository.dart';
import 'package:sahurpay/features/sessions/session_list_screen.dart';

void main() {
  testWidgets('SahurPay app starts on payment history', (tester) async {
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
  });
}
