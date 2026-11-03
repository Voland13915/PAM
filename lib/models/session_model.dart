// models/session_model.dart — кто вошёл. Вход остаётся локальной
// валидацией (L3): модель лишь запоминает введённые данные, чтобы их
// показал профиль. Проверка по серверу и JWT — на L5.
import 'package:flutter/foundation.dart';

class SessionModel extends ChangeNotifier {
  String? _name;
  String? _email;

  String? get email => _email;
  bool get isSignedIn => _email != null;

  /// Имя из регистрации, иначе часть e-mail до «@».
  String get displayName => _name ?? _email?.split('@').first ?? 'Гость';

  void signIn(String email) {
    if (email != _email) _name = null; // другой пользователь — другое имя
    _email = email;
    notifyListeners();
  }

  void register(String name, String email) {
    _name = name;
    _email = email;
    notifyListeners();
  }

  void signOut() {
    _name = null;
    _email = null;
    notifyListeners();
  }
}
