import 'package:flutter/foundation.dart';

import '../data/result.dart';
import '../data/wishlist_item.dart';
import '../data/wishlist_repository.dart';

class WishlistModel extends ChangeNotifier {
  WishlistModel(this._repository);

  final WishlistRepository _repository;

  bool _loading = false;
  String? _error;
  List<WishlistItem> _items = const [];

  bool get isLoading => _loading;
  String? get error => _error;
  List<WishlistItem> get items => List.unmodifiable(_items);

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

  Future<String?> add(WishlistItem draft) async {
    switch (await _repository.create(draft)) {
      case Ok(:final value):
        _items = [..._items, value];
        notifyListeners();
        return null;
      case Err(:final msg):
        return msg;
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
