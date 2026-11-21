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

String formatBytes(int bytes) {
  if (bytes < 1024) return '$bytes$_nbspБ';
  if (bytes < 1024 * 1024) return '${(bytes / 1024).round()}$_nbspКБ';
  final mb = (bytes / (1024 * 1024)).toStringAsFixed(1).replaceAll('.', ',');
  return '$mb$_nbspМБ';
}

String formatPercent(double value) =>
    '${value.toStringAsFixed(value < 10 ? 1 : 0).replaceAll('.', ',')}$_nbsp%';

String itemsWord(int count) {
  final n = count % 100;
  if (n >= 11 && n <= 14) return 'товаров';
  return switch (count % 10) {
    1 => 'товар',
    2 || 3 || 4 => 'товара',
    _ => 'товаров',
  };
}

String storesWord(int count) => count == 1 ? 'магазине' : 'магазинах';

const _months = [
  'янв', 'фев', 'мар', 'апр', 'мая', 'июн',
  'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
];

/// «12 ноя» — подпись точки на графике цены.
String formatShortDate(DateTime date) =>
    '${date.day}$_nbsp${_months[date.month - 1]}';

/// Время последнего обновления магазина: ISO-строка с сервера → «12 мин назад».
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

String formatNextRun(DateTime time, {DateTime? now}) {
  final current = now ?? DateTime.now();
  final today = DateTime(current.year, current.month, current.day);
  final day = DateTime(time.year, time.month, time.day);
  final clock = '${time.hour.toString().padLeft(2, '0')}:'
      '${time.minute.toString().padLeft(2, '0')}';
  final days = day.difference(today).inDays;
  if (days == 0) return 'сегодня в $clock';
  if (days == 1) return 'завтра в $clock';
  return '${formatShortDate(time)} в $clock';
}
