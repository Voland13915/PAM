import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/data/wishlist_item.dart';
import 'package:tech_price/models/catalog_model.dart';
import 'package:tech_price/models/shopping_list_model.dart';
import 'package:tech_price/models/wishlist_model.dart';

import 'fakes.dart';

void main() {
  test('ShoppingListModel: add/remove извещают подписчиков', () {
    final list = ShoppingListModel();
    var notified = 0;
    list.addListener(() => notified++);

    list.add(1);
    list.add(1);
    expect(list.count, 1);
    expect(notified, 1);

    list.remove(1);
    expect(list.count, 0);
    expect(notified, 2);
  });

  test('ShoppingListModel: список наружу только для чтения', () {
    final list = ShoppingListModel()..add(1);
    expect(() => list.productIds.add(2), throwsUnsupportedError);
  });

  test('CatalogModel: load приносит товары и магазины', () async {
    final catalog = CatalogModel(
      FakeProductRepository([product(1), product(2)]),
      FakeStoreRepository(),
    );
    await catalog.load();
    expect(catalog.isLoading, isFalse);
    expect(catalog.error, isNull);
    expect(catalog.products.length, 2);
    expect(catalog.storeName(2), 'Maximum');
    expect(catalog.byId(1)?.name, 'Товар 1');
  });

  test('CatalogModel: отказ превращается в сообщение, не в crash', () async {
    final products = FakeProductRepository([product(1)])..fail = true;
    final catalog = CatalogModel(products, FakeStoreRepository());
    await catalog.load();
    expect(catalog.error, failure);
    expect(catalog.products, isEmpty);
  });

  test('WishlistModel: add получает id от хранилища, remove удаляет',
      () async {
    final wishlist = WishlistModel(FakeWishlistRepository());
    await wishlist.load();

    expect(await wishlist.add(const WishlistItem(0, 3, 2, 5000)), isNull);
    final created = wishlist.byProduct(3)!;
    expect(created.id, isNot(0));

    expect(await wishlist.remove(created.id), isNull);
    expect(wishlist.byProduct(3), isNull);
  });

  test('WishlistModel: при отказе add возвращает ошибку, список не меняется',
      () async {
    final repository = FakeWishlistRepository();
    final wishlist = WishlistModel(repository);
    await wishlist.load();

    repository.fail = true;
    expect(await wishlist.add(const WishlistItem(0, 3, 2, 5000)), failure);
    expect(wishlist.items, isEmpty);
  });
}
