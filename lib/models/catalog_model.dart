import 'package:flutter/foundation.dart';

import '../data/product.dart';
import '../data/product_repository.dart';
import '../data/result.dart';
import '../data/store.dart';
import '../data/store_repository.dart';

class CatalogModel extends ChangeNotifier {
  CatalogModel(this._productRepository, this._storeRepository);

  final ProductRepository _productRepository;
  final StoreRepository _storeRepository;

  bool _loading = false;
  String? _error;
  List<Product> _products = const [];
  List<Store> _stores = const [];

  bool get isLoading => _loading;
  String? get error => _error;

  List<Product> get products => List.unmodifiable(_products);
  List<Store> get stores => List.unmodifiable(_stores);

  List<String> get categories =>
      List.unmodifiable(_products.map((p) => p.category).toSet());

  Product? byId(int id) {
    for (final p in _products) {
      if (p.id == id) return p;
    }
    return null;
  }

  Store? storeById(int id) {
    for (final s in _stores) {
      if (s.id == id) return s;
    }
    return null;
  }

  String storeName(int id) => storeById(id)?.name ?? '—';

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();

    final productsFuture = _productRepository.fetchAll();
    final storesFuture = _storeRepository.fetchAll();

    switch (await productsFuture) {
      case Ok(:final value):
        _products = value;
      case Err(:final msg):
        _error = msg;
    }
    switch (await storesFuture) {
      case Ok(:final value):
        _stores = value;
      case Err(:final msg):
        _error ??= msg;
    }

    _loading = false;
    notifyListeners();
  }
}
