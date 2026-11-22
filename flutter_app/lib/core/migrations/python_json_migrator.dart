import 'dart:convert';

import '../models/payment_models.dart';
import '../utils/money.dart';

class PythonJsonMigrator {
  const PythonJsonMigrator();

  List<PaymentSession> parseSessions(String source) {
    final decoded = jsonDecode(source);
    if (decoded is! Map<String, Object?>) {
      throw const FormatException(
        'The SahurPay backup must contain a JSON object.',
      );
    }

    final rawSessions = decoded['sessions'];
    if (rawSessions is! List) {
      throw const FormatException(
        'The SahurPay backup does not contain a sessions list.',
      );
    }

    final sessions = <PaymentSession>[];
    for (final rawSession in rawSessions) {
      sessions.add(_parseSession(rawSession));
    }
    return sessions;
  }

  PaymentSession _parseSession(Object? raw) {
    if (raw is! Map) {
      throw const FormatException('A saved session must be a JSON object.');
    }

    final peopleValues = raw['people'];
    if (peopleValues is! List) {
      throw const FormatException('A saved session must contain people.');
    }
    final people = peopleValues
        .map(Person.fromJson)
        .toList(growable: false);

    final receiptsValues = raw['receipts'];
    if (receiptsValues is! List) {
      throw const FormatException('A saved session must contain receipts.');
    }

    final receipts = receiptsValues
        .map((rawReceipt) => _parseReceipt(
              rawReceipt,
              people,
            ))
        .toList(growable: false);

    final dateValue = raw['date'];
    if (dateValue is! String) {
      throw const FormatException('A saved session must contain a date.');
    }
    final date = DateTime.tryParse(dateValue);
    if (date == null) {
      throw const FormatException(
        'A saved session contains an invalid ISO date.',
      );
    }

    final idValue = raw['id'];
    if (idValue is! String || idValue.trim().isEmpty) {
      throw const FormatException('A saved session must contain an id.');
    }

    return PaymentSession(
      id: idValue,
      date: date,
      people: people,
      receipts: receipts,
      category: _optionalString(raw['category']),
      note: _optionalString(raw['note']),
    );
  }

  StoreReceipt _parseReceipt(Object? raw, List<Person> people) {
    if (raw is! Map) {
      throw const FormatException('A saved receipt must be a JSON object.');
    }

    final storeName = raw['store'];
    if (storeName is! String || storeName.trim().isEmpty) {
      throw const FormatException('A saved receipt must contain a store.');
    }

    final payerName = raw['payer'];
    Person? payer;
    if (payerName is String) {
      payer = people.where((person) => person.name == payerName).firstOrNull;
      if (payer == null) {
        throw FormatException(
          'Unknown payer in saved receipt: $payerName.',
        );
      }
    }

    final itemsValue = raw['items'];
    if (itemsValue is! List) {
      throw const FormatException('A saved receipt must contain items.');
    }

    final items = itemsValue
        .map((rawItem) => _parseItem(rawItem, people))
        .toList(growable: false);

    return StoreReceipt(
      storeName: storeName,
      items: items,
      people: people,
      payer: payer,
      category: _optionalString(raw['category']),
      note: _optionalString(raw['note']),
    );
  }

  ReceiptItem _parseItem(Object? raw, List<Person> people) {
    if (raw is! Map) {
      throw const FormatException('A saved item must be a JSON object.');
    }

    final name = raw['name'];
    if (name is! String || name.trim().isEmpty) {
      throw const FormatException('A saved item must contain a name.');
    }

    final quantity = raw['quantity'];
    if (quantity is! int || quantity <= 0) {
      throw const FormatException(
        'A saved item must contain a positive quantity.',
      );
    }

    final unitPrice = raw['unit_price'];
    if (unitPrice is! String) {
      throw const FormatException(
        'A saved item must contain a unit_price string.',
      );
    }

    final participantsValue = raw['participants'];
    if (participantsValue is! List) {
      throw const FormatException(
        'A saved item must contain participants.',
      );
    }

    final participantNames = participantsValue.whereType<String>();
    final participants = participantNames
        .map((participantName) {
          return people
              .where((person) => person.name == participantName)
              .firstOrNull;
        })
        .whereType<Person>()
        .toList(growable: false);

    if (participants.isEmpty ||
        participants.length != participantNames.length) {
      throw const FormatException(
        'A saved item contains unknown or missing participants.',
      );
    }

    return ReceiptItem(
      product: Product(
        name: name,
        quantity: quantity,
        unitPriceCents: Money.centsFromString(unitPrice),
        category: _optionalString(raw['category']),
        note: _optionalString(raw['note']),
      ),
      participants: participants,
    );
  }

  String _optionalString(Object? value) {
    return value is String ? value : '';
  }
}

extension<T> on Iterable<T> {
  T? get firstOrNull {
    final iterator = this.iterator;
    if (!iterator.moveNext()) {
      return null;
    }
    return iterator.current;
  }
}
