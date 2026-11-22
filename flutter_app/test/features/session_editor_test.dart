import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sahurpay/features/sessions/session_editor_screen.dart';

void main() {
  testWidgets('shows validation before saving an empty session',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: SessionEditorScreen(),
      ),
    );

    await tester.tap(find.byKey(const Key('save-session-button')));
    await tester.pump();

    expect(find.text('Add at least one store.'), findsOneWidget);
  });

  testWidgets('adds a product and store to the session draft',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: SessionEditorScreen(),
      ),
    );

    Future<void> ensureVisibleAndEnter(Key key, String text) async {
      final finder = find.byKey(key);
      await tester.ensureVisible(finder);
      await tester.enterText(finder, text);
    }

    await ensureVisibleAndEnter(
      const Key('store-name-field'),
      'Corner Market',
    );
    await ensureVisibleAndEnter(
      const Key('product-name-field'),
      'Milk',
    );
    await ensureVisibleAndEnter(
      const Key('quantity-field'),
      '2',
    );
    await ensureVisibleAndEnter(
      const Key('price-field'),
      '2.50',
    );
    final personAChip = find.byType(FilterChip).first;
    await tester.ensureVisible(personAChip);
    final chip = tester.widget<FilterChip>(personAChip);
    chip.onSelected?.call(true);
    await tester.pump();
    final addProduct = find.byKey(const Key('add-product-button'));
    await tester.ensureVisible(addProduct);
    final productButton =
        tester.widget<OutlinedButton>(addProduct);
    productButton.onPressed?.call();
    await tester.pump();

    expect(find.text('Milk'), findsOneWidget);
    expect(find.text('2 × \$2.50'), findsOneWidget);

    final addStore = find.byKey(const Key('add-store-button'));
    await tester.ensureVisible(addStore);
    final storeButton =
        tester.widget<FilledButton>(addStore);
    storeButton.onPressed?.call();
    await tester.pump();

    expect(find.text('Added stores'), findsOneWidget);
    expect(find.text('Corner Market'), findsOneWidget);
  });
}
