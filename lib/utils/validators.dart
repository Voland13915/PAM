import 'formatters.dart';

String? validateEmail(String? value) {
  final email = value?.trim() ?? '';
  if (email.isEmpty) return 'Введите e-mail';
  final at = email.indexOf('@');
  if (at < 1 || at == email.length - 1) return 'Неверный формат e-mail';
  return null;
}

String? validatePassword(String? value) {
  if (value == null || value.isEmpty) return 'Введите пароль';
  if (value.length < 6) return 'Минимум 6 символов';
  return null;
}

String? validateName(String? value) {
  final name = value?.trim() ?? '';
  if (name.isEmpty) return 'Введите имя';
  if (name.length < 2) return 'Минимум 2 символа';
  return null;
}

String? validateTargetPrice(String? value, double currentBest) {
  final price = int.tryParse(value ?? '');
  if (price == null) return 'Введите цену';
  if (price <= 0) return 'Цена должна быть положительной';
  if (price >= currentBest) {
    return 'Должна быть ниже текущей цены (${formatPrice(currentBest)})';
  }
  return null;
}
