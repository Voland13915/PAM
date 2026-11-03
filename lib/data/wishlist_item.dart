// data/wishlist_item.dart — доменная модель слежения за ценой
// (вторая пишущая сущность темы: её создаёт форма «Следить за ценой»).

class WishlistItem {
  final int id; // идентичность записи; даёт хранилище (на L5 — сервер)
  final int productId;
  final int storeId;
  final double targetPrice; // желаемая цена
  final bool notify; // уведомить о снижении

  const WishlistItem(
    this.id,
    this.productId,
    this.storeId,
    this.targetPrice, {
    this.notify = true,
  });

  WishlistItem copyWith({
    int? id,
    int? storeId,
    double? targetPrice,
    bool? notify,
  }) =>
      WishlistItem(
        id ?? this.id,
        productId,
        storeId ?? this.storeId,
        targetPrice ?? this.targetPrice,
        notify: notify ?? this.notify,
      );
}
