import 'package:flutter_test/flutter_test.dart';

import 'package:sahurpay/main.dart';

void main() {
  testWidgets('SahurPay app starts on payment history', (tester) async {
    await tester.pumpWidget(const SahurPayApp());

    expect(find.text('SahurPay'), findsOneWidget);
    expect(find.text('Payment history'), findsOneWidget);
  });
}
