import 'package:flutter_test/flutter_test.dart';
import 'package:sahurpay/core/utils/money.dart';

void main() {
  test('parses decimal prices into exact cents', () {
    expect(Money.centsFromString('12.50'), 1250);
    expect(Money.centsFromString('3'), 300);
  });

  test('formats cents with a dollar sign', () {
    expect(Money.format(1250), r'$12.50');
    expect(Money.format(333), r'$3.33');
  });
}
