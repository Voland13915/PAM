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

const _months = [
  'янв', 'фев', 'мар', 'апр', 'мая', 'июн',
  'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
];

String formatShortDate(DateTime date) =>
    '${date.day}$_nbsp${_months[date.month - 1]}';

String formatSyncTime(String iso, {DateTime? now}) {
  final time = DateTime.tryParse(iso);
  if (time == null) return 'ещё не обновлялся';
  final diff = (now ?? DateTime.now()).toUtc().difference(time.toUtc());
  if (diff.inMinutes < 1) return 'только что';
  if (diff.inHours < 1) return '${diff.inMinutes}$_nbspмин назад';
  if (diff.inDays < 1) return '${diff.inHours}$_nbspч назад';
  if (diff.inDays < 7) return '${diff.inDays}$_nbspдн назад';
  return formatShortDate(time.toLocal());
}
