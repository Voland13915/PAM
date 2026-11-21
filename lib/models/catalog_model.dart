import 'package:flutter/foundation.dart';

import '../data/catalog_facets.dart';
import '../data/catalog_filter.dart';
import '../data/product.dart';
import '../data/product_repository.dart';
import '../data/result.dart';
import '../data/store.dart';
import '../data/store_repository.dart';
import '../data/sync_status.dart';

class CatalogModel extends ChangeNotifier {
  CatalogModel(this._productRepository, this._storeRepository, {this.storeId})
      : _filter = CatalogFilter(storeId: storeId);

  final ProductRepository _productRepository;
  final StoreRepository _storeRepository;
  final int? storeId;

  static const pageSize = 20;

  bool _loading = false;
  String? _error;
  List<Product> _products = const [];
  List<Store> _stores = const [];

  String _search = '';
  CatalogFilter _filter;
  CatalogFacets _facets = CatalogFacets.empty;
  int _page = 1;
  bool _hasMore = false;
  bool _loadingMore = false;
  String? _loadMoreError;
  int _generation = 0;

  final Map<int, Product> _known = {};
  final Map<String, List<String>> _images = {};
  final Set<int> _resolving = {};
  final Set<int> _missing = {};

  bool get isLoading => _loading;
  String? get error => _error;
  String get search => _search;
  CatalogFilter get filter => _filter;
  CatalogFacets get facets => _facets;
  bool get hasMore => _hasMore;
  bool get isLoadingMore => _loadingMore;
  String? get loadMoreError => _loadMoreError;

  bool get isResolving => _resolving.isNotEmpty;

  int get activeFilters => _filter.activeCount - (storeId != null ? 1 : 0);

  List<Product> get products => List.unmodifiable(_products);
  List<Store> get stores => List.unmodifiable(_stores);

  List<String> get categories =>
      List.unmodifiable(_facets.categories.map((c) => c.name));

  Product? byId(int id) {
    final known = _known[id];
    if (known != null) return known;
    if (!_loading && _error == null) _resolve(id);
    return null;
  }

  Store? storeById(int id) {
    for (final s in _stores) {
      if (s.id == id) return s;
    }
    return null;
  }

  String storeName(int id) => storeById(id)?.name ?? '—';

  Future<List<String>> images(int productId, {String color = ''}) async {
    final key = '$productId/$color';
    final cached = _images[key];
    if (cached != null) return cached;
    switch (await _productRepository.fetchImages(productId, color: color)) {
      case Ok(:final value):
        _images[key] = value;
        return value;
      case Err():
        return const [];
    }
  }

  Future<Result<SyncStatus>> syncStatus() => _storeRepository.fetchSync();

  Future<Result<SyncStatus>> startSync() => _storeRepository.startSync();

  Future<void> applyFilter(CatalogFilter filter) {
    _filter = storeId == null ? filter : filter.copyWith(storeId: () => storeId);
    return load();
  }

  Future<void> load({String? search}) async {
    _search = search ?? _search;
    _page = 1;
    final generation = ++_generation;
    _loading = true;
    _error = null;
    _loadMoreError = null;
    _missing.clear();
    notifyListeners();

    final productsFuture = _productRepository.fetchAll(
        page: 1, limit: pageSize, search: _search, filter: _filter);
    final facetsFuture =
        _productRepository.fetchFacets(search: _search, filter: _filter);
    final storesFuture = _storeRepository.fetchAll();

    final products = await productsFuture;
    final facets = await facetsFuture;
    final stores = await storesFuture;
    if (generation != _generation) return;

    switch (products) {
      case Ok(:final value):
        _products = value;
        _hasMore = value.length == pageSize;
        _remember(value);
      case Err(:final msg):
        _error = msg;
    }
    switch (stores) {
      case Ok(:final value):
        _stores = value;
      case Err(:final msg):
        _error ??= msg;
    }
    if (facets case Ok(:final value)) {
      _facets = value;
    }

    _loading = false;
    notifyListeners();
  }

  Future<void> loadMore() async {
    if (_loadingMore || _loading || !_hasMore || _loadMoreError != null) {
      return;
    }
    _loadingMore = true;
    final generation = _generation;

    final result = await _productRepository.fetchAll(
        page: _page + 1, limit: pageSize, search: _search, filter: _filter);
    if (generation != _generation) {
      _loadingMore = false;
      notifyListeners();
      return;
    }

    switch (result) {
      case Ok(:final value):
        _page += 1;
        _products = [..._products, ...value];
        _hasMore = value.length == pageSize;
        _remember(value);
      case Err(:final msg):
        _loadMoreError = msg;
    }
    _loadingMore = false;
    notifyListeners();
  }

  void retryLoadMore() {
    _loadMoreError = null;
    notifyListeners();
  }

  void _remember(List<Product> products) {
    for (final p in products) {
      _known[p.id] = p;
    }
  }

  void _resolve(int id) {
    if (_missing.contains(id) || !_resolving.add(id)) return;
    _productRepository.fetchById(id).then((result) {
      _resolving.remove(id);
      switch (result) {
        case Ok(:final value):
          _known[id] = value;
        case Err():
          _missing.add(id);
      }
      notifyListeners();
    });
  }
}
