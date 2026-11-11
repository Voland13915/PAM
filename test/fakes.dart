import 'package:tech_price/data/product.dart';
import 'package:tech_price/data/product_repository.dart';
import 'package:tech_price/data/result.dart';
import 'package:tech_price/data/store.dart';
import 'package:tech_price/data/store_repository.dart';
import 'package:tech_price/data/wishlist_item.dart';
import 'package:tech_price/data/wishlist_repository.dart';

const failure = 'Сервер не отвечает';

Product product(int id, {String name = 'Товар', String category = 'Смартфоны'}) =>
    Product(
      id: id,
      name: '$name $id',
      brand: 'Brand',
      category: category,
      specs: const {},
      offers: const [Offer(1, 1000), Offer(2, 900)],
      priceHistory: const [1000, 900],
    );

class FakeProductRepository implements ProductRepository {
  FakeProductRepository(this.items);

  final List<Product> items;
  bool fail = false;
  final List<int> requestedPages = [];

  @override
  Future<Result<List<Product>>> fetchAll(
      {int page = 1, int limit = 20, String? search}) async {
    requestedPages.add(page);
    if (fail) return const Err(failure);
    final filtered = search == null || search.isEmpty
        ? items
        : items
            .where((p) => p.name.toLowerCase().contains(search.toLowerCase()))
            .toList();
    return Ok(filtered.skip((page - 1) * limit).take(limit).toList());
  }

  @override
  Future<Result<Product>> fetchById(int id) async {
    if (fail) return const Err(failure);
    for (final p in items) {
      if (p.id == id) return Ok(p);
    }
    return const Err('Запись не существует');
  }

  @override
  Future<Result<Product>> create(Product product) async =>
      Ok(product.copyWith(id: items.length + 1000));

  @override
  Future<Result<Product>> update(Product product) async => Ok(product);

  @override
  Future<Result<void>> delete(int id) async => const Ok(null);
}

class FakeStoreRepository implements StoreRepository {
  bool fail = false;

  @override
  Future<Result<List<Store>>> fetchAll() async => fail
      ? const Err(failure)
      : const Ok([
          Store(1, 'Bomba', 'bomba.md', 10, ''),
          Store(2, 'Maximum', 'maximum.md', 10, ''),
        ]);
}

class FakeWishlistRepository implements WishlistRepository {
  final List<WishlistItem> _items = [];
  int _nextId = 1;
  bool fail = false;

  @override
  Future<Result<List<WishlistItem>>> fetchAll() async =>
      fail ? const Err(failure) : Ok(List.of(_items));

  @override
  Future<Result<WishlistItem>> fetchById(int id) async {
    for (final i in _items) {
      if (i.id == id) return Ok(i);
    }
    return const Err('Запись не существует');
  }

  @override
  Future<Result<WishlistItem>> create(WishlistItem item) async {
    if (fail) return const Err(failure);
    final created = item.copyWith(id: _nextId++);
    _items.add(created);
    return Ok(created);
  }

  @override
  Future<Result<WishlistItem>> update(WishlistItem item) async {
    if (fail) return const Err(failure);
    final index = _items.indexWhere((i) => i.id == item.id);
    if (index == -1) return const Err('Запись не существует');
    _items[index] = item;
    return Ok(item);
  }

  @override
  Future<Result<void>> delete(int id) async {
    if (fail) return const Err(failure);
    _items.removeWhere((i) => i.id == id);
    return const Ok(null);
  }
}
