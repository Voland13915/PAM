// data/mock_wishlist_repository.dart — слежения за ценой в памяти.
import 'mock_data.dart';
import 'mock_network.dart';
import 'result.dart';
import 'wishlist_item.dart';
import 'wishlist_repository.dart';

class MockWishlistRepository implements WishlistRepository {
  MockWishlistRepository(this._network);

  final MockNetwork _network;
  final List<WishlistItem> _items = List.of(mockWishlist);
  int _nextId = 1000;

  static const _notFound = 'Слежение не существует';

  @override
  Future<Result<List<WishlistItem>>> fetchAll() async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    return Ok(List.of(_items));
  }

  @override
  Future<Result<WishlistItem>> fetchById(int id) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final index = _items.indexWhere((i) => i.id == id);
    if (index == -1) return const Err(_notFound);
    return Ok(_items[index]);
  }

  @override
  Future<Result<WishlistItem>> create(WishlistItem item) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final created = item.copyWith(id: _nextId++);
    _items.add(created);
    return Ok(created);
  }

  @override
  Future<Result<WishlistItem>> update(WishlistItem item) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final index = _items.indexWhere((i) => i.id == item.id);
    if (index == -1) return const Err(_notFound);
    _items[index] = item;
    return Ok(item);
  }

  @override
  Future<Result<void>> delete(int id) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final before = _items.length;
    _items.removeWhere((i) => i.id == id);
    if (_items.length == before) return const Err(_notFound);
    return const Ok(null);
  }
}
