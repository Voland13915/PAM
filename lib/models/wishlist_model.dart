// models/wishlist_model.dart — разделяемое состояние «Избранного»:
// слежения за ценой. Их пишет форма «Следить за ценой», читают вкладка
// «Избранное», детали товара (сердечко) и профиль (счётчик).
import 'package:flutter/foundation.dart';

import '../data/result.dart';
import '../data/wishlist_item.dart';
import '../data/wishlist_repository.dart';

class WishlistModel extends ChangeNotifier {
  WishlistModel(this._repository); // DI через конструктор

  final WishlistRepository _repository; // тип — интерфейс, не mock

  bool _loading = false;
  String? _error;
  List<WishlistItem> _items = const [];

  bool get isLoading => _loading;
  String? get error => _error;
  List<WishlistItem> get items => List.unmodifiable(_items);

  /// Слежение за конкретным товаром или null, если его нет.
  WishlistItem? byProduct(int productId) {
    for (final item in _items) {
      if (item.productId == productId) return item;
    }
    return null;
  }

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();

    switch (await _repository.fetchAll()) {
      case Ok(:final value):
        _items = value;
      case Err(:final msg):
        _error = msg;
    }

    _loading = false;
    notifyListeners();
  }

  // Мутации: вердикт хранилища → мутация → извещение.
  // Конвенция возврата как у validator (C6): null — успех, текст — ошибка.

  Future<String?> add(WishlistItem draft) async {
    switch (await _repository.create(draft)) {
      case Ok(:final value):
        _items = [..._items, value]; // с id-ом, выданным хранилищем
        notifyListeners();
        return null;
      case Err(:final msg):
        return msg; // состояние нетронуто — экран решает, что показать
    }
  }

  Future<String?> update(WishlistItem item) async {
    switch (await _repository.update(item)) {
      case Ok(:final value):
        _items = [for (final i in _items) i.id == value.id ? value : i];
        notifyListeners();
        return null;
      case Err(:final msg):
        return msg;
    }
  }

  Future<String?> remove(int id) async {
    switch (await _repository.delete(id)) {
      case Ok():
        _items = _items.where((i) => i.id != id).toList();
        notifyListeners();
        return null;
      case Err(:final msg):
        return msg;
    }
  }
}
