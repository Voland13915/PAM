import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class TokenStore {
  TokenStore({FlutterSecureStorage? storage})
      : _storage = storage ?? FlutterSecureStorage();

  static const _key = 'auth_token';

  final FlutterSecureStorage _storage;

  String? _cached;
  bool _loaded = false;

  Future<String?> read() async {
    if (_loaded) return _cached;
    try {
      _cached = await _storage.read(key: _key) ?? await _migrateLegacy();
    } on PlatformException {
      await _storage.delete(key: _key);
      _cached = null;
    }
    _loaded = true;
    return _cached;
  }

  Future<void> save(String token) async {
    await _storage.write(key: _key, value: token);
    _cached = token;
    _loaded = true;
  }

  Future<void> clear() async {
    await _storage.delete(key: _key);
    _cached = null;
    _loaded = true;
  }

  Future<String?> _migrateLegacy() async {
    final prefs = await SharedPreferences.getInstance();
    final legacy = prefs.getString(_key);
    if (legacy == null) return null;
    await _storage.write(key: _key, value: legacy);
    await prefs.remove(_key);
    return legacy;
  }
}
