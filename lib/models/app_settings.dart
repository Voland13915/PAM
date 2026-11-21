import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum SavingsBaseline { highest, average }

class AppSettings extends ChangeNotifier {
  AppSettings(this._prefs);

  static Future<AppSettings> load() async =>
      AppSettings(await SharedPreferences.getInstance());

  static const notificationsKey = 'settings_notifications';
  static const _themeKey = 'settings_theme';
  static const _baselineKey = 'settings_savings_baseline';

  final SharedPreferences _prefs;

  static Future<bool> notificationsAllowed() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    return prefs.getBool(notificationsKey) ?? true;
  }

  bool get notifications => _prefs.getBool(notificationsKey) ?? true;

  ThemeMode get themeMode =>
      ThemeMode.values.asNameMap()[_prefs.getString(_themeKey)] ??
      ThemeMode.system;

  SavingsBaseline get savingsBaseline =>
      SavingsBaseline.values.asNameMap()[_prefs.getString(_baselineKey)] ??
      SavingsBaseline.highest;

  Future<void> setNotifications(bool value) async {
    if (value == notifications) return;
    await _prefs.setBool(notificationsKey, value);
    notifyListeners();
  }

  Future<void> setThemeMode(ThemeMode value) async {
    if (value == themeMode) return;
    await _prefs.setString(_themeKey, value.name);
    notifyListeners();
  }

  Future<void> setSavingsBaseline(SavingsBaseline value) async {
    if (value == savingsBaseline) return;
    await _prefs.setString(_baselineKey, value.name);
    notifyListeners();
  }
}
