import 'package:flutter/foundation.dart';

class OfflineStatus extends ChangeNotifier {
  DateTime? _savedAt;

  bool get isOffline => _savedAt != null;

  DateTime? get savedAt => _savedAt;

  void showingCached(DateTime savedAt) {
    final current = _savedAt;
    if (current != null && !savedAt.isBefore(current)) return;
    _savedAt = savedAt;
    notifyListeners();
  }

  void online() {
    if (_savedAt == null) return;
    _savedAt = null;
    notifyListeners();
  }
}
