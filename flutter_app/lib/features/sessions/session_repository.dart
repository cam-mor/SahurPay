import '../../core/models/payment_models.dart';

abstract interface class SessionRepository {
  List<PaymentSession> loadSessions();
}

class InMemorySessionRepository implements SessionRepository {
  const InMemorySessionRepository();

  @override
  List<PaymentSession> loadSessions() {
    const people = [
      Person('A'),
      Person('B'),
      Person('C'),
    ];

    const milk = ReceiptItem(
      product: Product(
        name: 'Milk',
        quantity: 2,
        unitPriceCents: 250,
        category: 'Groceries',
        note: 'Room milk',
      ),
      participants: [Person('A'), Person('B')],
    );
    const snacks = ReceiptItem(
      product: Product(
        name: 'Snacks',
        quantity: 1,
        unitPriceCents: 800,
        category: 'Shared',
      ),
      participants: [Person('A'), Person('B'), Person('C')],
    );
    const soap = ReceiptItem(
      product: Product(
        name: 'Soap',
        quantity: 2,
        unitPriceCents: 225,
        category: 'Household',
      ),
      participants: [Person('C')],
    );

    return [
      PaymentSession(
        id: 'sample-1',
        date: DateTime(2026, 11, 21),
        people: people,
        category: 'Household',
        note: 'A small shopping run',
        receipts: [
          const StoreReceipt(
            storeName: 'Corner Market',
            people: people,
            payer: Person('A'),
            category: 'Groceries',
            note: 'Weekly basics',
            items: [milk, snacks],
          ),
          const StoreReceipt(
            storeName: 'Pharmacy',
            people: people,
            payer: Person('B'),
            category: 'Household',
            items: [soap],
          ),
        ],
      ),
    ];
  }
}
