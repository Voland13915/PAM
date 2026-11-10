import 'package:flutter/foundation.dart';

class SessionModel extends ChangeNotifier {
  String? _name;
  String? _email;

  String? get email => _email;
  bool get isSignedIn => _email != null;

  String get displayName => _name ?? _email?.split('@').first ?? 'Гость';

  void signIn(String email) {
    if (email != _email) _name = null;
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
