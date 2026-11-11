import 'api_client.dart';
import 'result.dart';
import 'wishlist_item.dart';
import 'wishlist_repository.dart';

class HttpWishlistRepository implements WishlistRepository {
  HttpWishlistRepository(this._api);

  final ApiClient _api;

  WishlistItem _item(Object? json) =>
      WishlistItem.fromJson(json as Map<String, dynamic>);

  @override
  Future<Result<List<WishlistItem>>> fetchAll() => _api.send(
        'GET',
        '/wishlist',
        query: {'limit': '100'},
        parse: (json) => pageItems(json, WishlistItem.fromJson),
      );

  @override
  Future<Result<WishlistItem>> fetchById(int id) =>
      _api.send('GET', '/wishlist/$id', parse: _item);

  @override
  Future<Result<WishlistItem>> create(WishlistItem item) => _api.send(
        'POST',
        '/wishlist',
        body: item.toJson(),
        okStatus: 201,
        parse: _item,
      );

  @override
  Future<Result<WishlistItem>> update(WishlistItem item) => _api.send(
        'PUT',
        '/wishlist/${item.id}',
        body: item.toJson(),
        parse: _item,
      );

  @override
  Future<Result<void>> delete(int id) => _api.send(
        'DELETE',
        '/wishlist/$id',
        okStatus: 204,
        parse: (_) {},
      );
}
