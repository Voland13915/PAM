class WishlistItem {
  final int id;
  final int productId;
  final int storeId;
  final double targetPrice;
  final bool notify;

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
