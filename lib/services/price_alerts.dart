import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../data/product.dart';
import '../data/wishlist_item.dart';

class PriceAlert {
  final WishlistItem item;
  final Product product;
  final Offer offer;

  const PriceAlert(this.item, this.product, this.offer);
}

List<PriceAlert> findAlerts(
  List<WishlistItem> items,
  Map<int, Product> products,
  Map<int, double> notified,
) {
  final alerts = <PriceAlert>[];
  for (final item in items) {
    if (!item.notify) continue;
    final product = products[item.productId];
    if (product == null || !product.isAvailable) continue;
    final best = product.bestOffer;
    if (best.price > item.targetPrice) continue;
    final last = notified[item.id];
    if (last != null && best.price >= last) continue;
    alerts.add(PriceAlert(item, product, best));
  }
  return alerts;
}

Map<int, double> rememberAlerts(
  List<WishlistItem> items,
  Map<int, Product> products,
  Map<int, double> notified,
  List<PriceAlert> sent,
) {
  final result = <int, double>{};
  for (final item in items) {
    final product = products[item.productId];
    if (product == null) {
      final last = notified[item.id];
      if (last != null) result[item.id] = last;
      continue;
    }
    final reached =
        product.isAvailable && product.bestOffer.price <= item.targetPrice;
    final last = notified[item.id];
    if (reached && last != null) result[item.id] = last;
  }
  for (final alert in sent) {
    result[alert.item.id] = alert.offer.price;
  }
  return result;
}

class NotifiedPrices {
  static const _key = 'price_alerts_notified';

  Future<Map<int, double>> load() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    final raw = prefs.getString(_key);
    if (raw == null) return {};
    try {
      final data = jsonDecode(raw) as Map<String, dynamic>;
      return {
        for (final entry in data.entries)
          int.parse(entry.key): (entry.value as num).toDouble(),
      };
    } on FormatException {
      return {};
    }
  }

  Future<void> save(Map<int, double> prices) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _key,
      jsonEncode({for (final e in prices.entries) '${e.key}': e.value}),
    );
  }
}
