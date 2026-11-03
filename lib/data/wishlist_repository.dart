// data/wishlist_repository.dart — вторая пишущая сущность темы:
// слежение за ценой (форма «Следить за ценой», вкладка «Избранное»).
import 'result.dart';
import 'wishlist_item.dart';

abstract class WishlistRepository {
  Future<Result<List<WishlistItem>>> fetchAll(); //   L5: GET    /wishlist
  Future<Result<WishlistItem>> fetchById(int id); //  L5: GET    /wishlist/{id}
  Future<Result<WishlistItem>> create(WishlistItem item); // POST /wishlist
  Future<Result<WishlistItem>> update(WishlistItem item); // PUT  /wishlist/{id}
  Future<Result<void>> delete(int id); //             L5: DELETE /wishlist/{id}
}
