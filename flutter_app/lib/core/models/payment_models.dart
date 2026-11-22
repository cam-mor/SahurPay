import '../utils/money.dart';

class Person {
  const Person(this.name);

  final String name;

  factory Person.fromJson(Object? value) {
    if (value is! String || value.trim().isEmpty) {
      throw const FormatException('Person names cannot be empty.');
    }
    return Person(value.trim());
  }

  Map<String, Object?> toJson() => {'name': name};

  @override
  bool operator ==(Object other) => other is Person && other.name == name;

  @override
  int get hashCode => name.hashCode;

  @override
  String toString() => name;
}

class Product {
  const Product({
    required this.name,
    required this.quantity,
    required this.unitPriceCents,
    this.category = '',
    this.note = '',
  });

  final String name;
  final int quantity;
  final int unitPriceCents;
  final String category;
  final String note;

  int get totalCents => unitPriceCents * quantity;

  String get totalLabel => Money.format(totalCents);

  Product copyWith({
    String? name,
    int? quantity,
    int? unitPriceCents,
    String? category,
    String? note,
  }) {
    return Product(
      name: name ?? this.name,
      quantity: quantity ?? this.quantity,
      unitPriceCents: unitPriceCents ?? this.unitPriceCents,
      category: category ?? this.category,
      note: note ?? this.note,
    );
  }
}

class ReceiptItem {
  const ReceiptItem({
    required this.product,
    required this.participants,
  });

  final Product product;
  final List<Person> participants;

  Map<String, int> get allocations {
    if (participants.isEmpty) {
      return const {};
    }

    final base = product.totalCents ~/ participants.length;
    final remainder =
        (product.totalCents - base * participants.length).clamp(
      0,
      participants.length,
    ).toInt();

    final result = <String, int>{};
    for (var index = 0; index < participants.length; index++) {
      result[participants[index].name] =
          base + (index < remainder ? 1 : 0);
    }
    return result;
  }
}

class StoreReceipt {
  const StoreReceipt({
    required this.storeName,
    required this.items,
    required this.people,
    this.payer,
    this.category = '',
    this.note = '',
  });

  final String storeName;
  final List<ReceiptItem> items;
  final List<Person> people;
  final Person? payer;
  final String category;
  final String note;

  int get totalCents =>
      items.fold(0, (total, item) => total + item.product.totalCents);

  String get totalLabel => Money.format(totalCents);
}

class PaymentSession {
  const PaymentSession({
    required this.id,
    required this.date,
    required this.people,
    required this.receipts,
    this.category = '',
    this.note = '',
  });

  final String id;
  final DateTime date;
  final List<Person> people;
  final List<StoreReceipt> receipts;
  final String category;
  final String note;

  int get totalCents =>
      receipts.fold(0, (total, receipt) => total + receipt.totalCents);

  String get totalLabel => Money.format(totalCents);

  Map<String, int> personTotals() {
    final totals = <String, int>{
      for (final person in people) person.name: 0,
    };
    for (final receipt in receipts) {
      for (final item in receipt.items) {
        for (final entry in item.allocations.entries) {
          totals[entry.key] = (totals[entry.key] ?? 0) - entry.value;
        }
      }
      if (receipt.payer != null) {
        totals[receipt.payer!.name] =
            (totals[receipt.payer!.name] ?? 0) + receipt.totalCents;
      }
    }
    return totals;
  }
}
