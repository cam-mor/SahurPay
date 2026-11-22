class Money {
  const Money._();

  static int centsFromString(String value) {
    final normalized = value.trim();
    if (normalized.isEmpty) {
      throw const FormatException('A price is required.');
    }

    final negative = normalized.startsWith('-');
    final unsigned = normalized.replaceFirst(RegExp(r'^-'), '');
    final parts = unsigned.split('.');
    if (parts.isEmpty || parts.length > 2) {
      throw const FormatException('Use a price such as 12.50.');
    }

    final dollars = parts.first.isEmpty ? 0 : int.tryParse(parts.first);
    if (dollars == null) {
      throw const FormatException('Use a price such as 12.50.');
    }
    final fraction = parts.length == 2 ? parts[1] : '';
    if (fraction.length > 2) {
      throw const FormatException('Use no more than two decimal places.');
    }
    final cents = int.tryParse(fraction.padRight(2, '0')) ?? -1;
    if (cents < 0) {
      throw const FormatException('Use a price such as 12.50.');
    }
    final total = dollars * 100 + cents;
    return negative ? -total : total;
  }

  static String format(int cents) {
    final negative = cents < 0;
    final absolute = cents.abs();
    final dollars = absolute ~/ 100;
    final remainder = (absolute % 100).toString().padLeft(2, '0');
    return '${negative ? '-' : ''}\$$dollars.$remainder';
  }

  static String formatSigned(int cents) {
    if (cents > 0) {
      return '+${format(cents)}';
    }
    if (cents < 0) {
      return '-${format(cents.abs())}';
    }
    return format(cents);
  }
}
