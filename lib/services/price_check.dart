import 'package:flutter/foundation.dart';

import '../data/api_client.dart';
import '../data/http_product_repository.dart';
import '../data/http_store_repository.dart';
import '../data/http_wishlist_repository.dart';
import '../data/product.dart';
import '../data/result.dart';
import '../data/token_store.dart';
import '../data/wishlist_item.dart';
import 'notifications.dart';
import 'price_alerts.dart';

Future<int> runPriceCheck(String apiBase, {TokenStore? tokens}) async {
  final store = tokens ?? TokenStore();
  if (await store.read() == null) return 0;
  final api = ApiClient(apiBase, store);

  final wishlist = await HttpWishlistRepository(api).fetchAll();
  if (wishlist is! Ok<List<WishlistItem>>) return 0;
  final watched = wishlist.value.where((item) => item.notify).toList();
  if (watched.isEmpty) return 0;

  final productRepository = HttpProductRepository(api);
  final products = <int, Product>{};
  for (final item in watched) {
    if (products.containsKey(item.productId)) continue;
    final result = await productRepository.fetchById(item.productId);
    if (result case Ok(:final value)) products[item.productId] = value;
  }

  final names = <int, String>{};
  if (await HttpStoreRepository(api).fetchAll() case Ok(:final value)) {
    for (final s in value) {
      names[s.id] = s.name;
    }
  }

  for (final item in watched) {
    final product = products[item.productId];
    debugPrint(product == null
        ? 'Товар ${item.productId} не загрузился'
        : '${product.name}: лучшая ${product.bestOffer.price}, '
            'цель ${item.targetPrice}, в наличии ${product.isAvailable}');
  }

  final memory = NotifiedPrices();
  final notified = await memory.load();
  final alerts = findAlerts(watched, products, notified);
  for (final alert in alerts) {
    await Notifications.showAlert(
        alert, names[alert.offer.storeId] ?? 'магазине');
  }
  await memory.save(rememberAlerts(watched, products, notified, alerts));
  return alerts.length;
}
