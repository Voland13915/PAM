import 'result.dart';
import 'wishlist_item.dart';

abstract class WishlistRepository {
  Future<Result<List<WishlistItem>>> fetchAll();
  Future<Result<WishlistItem>> fetchById(int id);
  Future<Result<WishlistItem>> create(WishlistItem item);
  Future<Result<WishlistItem>> update(WishlistItem item);
  Future<Result<void>> delete(int id);
}
