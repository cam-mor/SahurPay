import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

import '../../core/migrations/python_json_migrator.dart';
import '../../core/models/payment_models.dart';

abstract interface class SessionRepositoryInterface {
  List<PaymentSession> get sessions;
  Future<void> initialize();
  Future<void> addSession(PaymentSession session);
  Future<void> deleteSession(String id);
}

class SessionRepository
    with ChangeNotifier
    implements SessionRepositoryInterface {
  SessionRepository();

  List<PaymentSession> _sessions = [];
  File? _storageFile;
  bool _initialized = false;

  @override
  List<PaymentSession> get sessions =>
      List<PaymentSession>.unmodifiable(_sessions);

  @override
  Future<void> initialize() async {
    if (_initialized) {
      return;
    }
    _initialized = true;

    try {
      final directory = await getApplicationDocumentsDirectory();
      final sahurpayDirectory =
          Directory('${directory.path}${Platform.pathSeparator}SahurPay');
      await sahurpayDirectory.create(recursive: true);
      _storageFile = File(
        '${sahurpayDirectory.path}${Platform.pathSeparator}sahurpay_sessions.json',
      );

      if (await _storageFile!.exists()) {
        _sessions = const PythonJsonMigrator().parseSessions(
          await _storageFile!.readAsString(),
        );
      } else {
        await _tryMigratePythonJson();
      }
    } on FileSystemException {
      _sessions = [];
    } on FormatException {
      _sessions = [];
    }

    notifyListeners();
  }

  Future<void> _tryMigratePythonJson() async {
    for (final path in const [
      '../data/sessions.json',
      'data/sessions.json',
      '../../data/sessions.json',
    ]) {
      final file = File(path);
      if (!await file.exists()) {
        continue;
      }
      final migrated = const PythonJsonMigrator().parseSessions(
        await file.readAsString(),
      );
      _sessions = migrated;
      await _save();
      return;
    }
  }

  @override
  Future<void> addSession(PaymentSession session) async {
    _sessions = [
      session,
      ..._sessions.where((existing) => existing.id != session.id),
    ];
    await _save();
    notifyListeners();
  }

  @override
  Future<void> deleteSession(String id) async {
    _sessions = _sessions.where((session) => session.id != id).toList();
    await _save();
    notifyListeners();
  }

  Future<void> _save() async {
    final file = _storageFile;
    if (file == null) {
      return;
    }
    await file.writeAsString(
      jsonEncode({
        'version': 1,
        'sessions': _sessions.map(_sessionToJson).toList(),
      }),
      flush: true,
    );
  }

  Map<String, Object?> _sessionToJson(PaymentSession session) {
    return {
      'id': session.id,
      'date':
          '${session.date.year.toString().padLeft(4, '0')}-'
          '${session.date.month.toString().padLeft(2, '0')}-'
          '${session.date.day.toString().padLeft(2, '0')}',
      'category': session.category,
      'note': session.note,
      'people': session.people.map((person) => person.name).toList(),
      'receipts': session.receipts.map((receipt) {
        return {
          'store': receipt.storeName,
          'payer': receipt.payer?.name,
          'category': receipt.category,
          'note': receipt.note,
          'items': receipt.items.map((item) {
            return {
              'name': item.product.name,
              'quantity': item.product.quantity,
              'unit_price':
                  '${(item.product.unitPriceCents ~/ 100).toString()}.${(item.product.unitPriceCents % 100).abs().toString().padLeft(2, '0')}',
              'category': item.product.category,
              'note': item.product.note,
              'participants':
                  item.participants.map((person) => person.name).toList(),
            };
          }).toList(),
        };
      }).toList(),
    };
  }
}

class InMemorySessionRepository {
  const InMemorySessionRepository();

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
