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

  factory WishlistItem.fromJson(Map<String, dynamic> j) => WishlistItem(
        j['id'] as int,
        j['productId'] as int,
        j['storeId'] as int,
        (j['targetPrice'] as num).toDouble(),
        notify: j['notify'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'productId': productId,
        'storeId': storeId,
        'targetPrice': targetPrice,
        'notify': notify,
      };

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
