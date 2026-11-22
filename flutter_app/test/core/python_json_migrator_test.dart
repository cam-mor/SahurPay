import 'package:flutter_test/flutter_test.dart';
import 'package:sahurpay/core/migrations/python_json_migrator.dart';

void main() {
  test('migrates Python JSON sessions with categories and payer', () {
    const source = '''
{
  "version": 1,
  "sessions": [
    {
      "id": "session-1",
      "date": "2026-11-21",
      "category": "Household",
      "note": "Weekly run",
      "people": ["A", "B", "C"],
      "receipts": [
        {
          "store": "Market",
          "payer": "A",
          "category": "Groceries",
          "note": "Room basics",
          "items": [
            {
              "name": "Milk",
              "quantity": 2,
              "unit_price": "2.50",
              "participants": ["A", "B"],
              "category": "Dairy",
              "note": "Whole milk"
            }
          ]
        }
      ]
    }
  ]
}
''';

    final sessions =
        const PythonJsonMigrator().parseSessions(source);

    expect(sessions, hasLength(1));
    expect(sessions.first.id, 'session-1');
    expect(sessions.first.category, 'Household');
    expect(sessions.first.receipts.first.storeName, 'Market');
    expect(sessions.first.receipts.first.payer?.name, 'A');
    expect(sessions.first.receipts.first.totalCents, 500);
    expect(
      sessions.first.receipts.first.items.first.product.note,
      'Whole milk',
    );
  });

  test('rejects malformed JSON shape', () {
    expect(
      () => const PythonJsonMigrator().parseSessions('[]'),
      throwsA(isA<FormatException>()),
    );
  });
}
