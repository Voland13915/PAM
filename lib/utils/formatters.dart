const _nbsp = '\u00A0';

String formatNumber(double value) {
  final digits = value.round().toString();
  final buffer = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) buffer.write(_nbsp);
    buffer.write(digits[i]);
  }
  return buffer.toString();
}

String formatPrice(double value) => '${formatNumber(value)}${_nbsp}MDL';

String storesWord(int count) => count == 1 ? 'магазине' : 'магазинах';
