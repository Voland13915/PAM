// test/models_test.dart — модели проверяются без единого widget-а:
// это логика темы на чистом Dart. Задержка mock-сети обнулена.
import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/data/mock_network.dart';
import 'package:tech_price/data/mock_product_repository.dart';
import 'package:tech_price/data/mock_store_repository.dart';
import 'package:tech_price/data/mock_wishlist_repository.dart';
import 'package:tech_price/data/wishlist_item.dart';
import 'package:tech_price/models/catalog_model.dart';
import 'package:tech_price/models/shopping_list_model.dart';
import 'package:tech_price/models/wishlist_model.dart';

void main() {
  late MockNetwork network;

  setUp(() => network = MockNetwork(latency: Duration.zero));

  test('ShoppingListModel: add/remove извещают подписчиков', () {
    final list = ShoppingListModel();
    var notified = 0;
    list.addListener(() => notified++);

    list.add(1);
    list.add(1); // повтор — мутации нет, извещения нет
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
      MockProductRepository(network),
      MockStoreRepository(network),
    );
    await catalog.load();
    expect(catalog.isLoading, isFalse);
    expect(catalog.error, isNull);
    expect(catalog.products, isNotEmpty);
    expect(catalog.stores, isNotEmpty);
    expect(catalog.byId(1)?.name, contains('Samsung'));
  });

  test('CatalogModel: авария превращается в сообщение, не в crash', () async {
    network.simulateError = true;
    final catalog = CatalogModel(
      MockProductRepository(network),
      MockStoreRepository(network),
    );
    await catalog.load();
    expect(catalog.error, MockNetwork.errorMessage);
    expect(catalog.products, isEmpty);
  });

  test('WishlistModel: add получает id от хранилища, remove удаляет',
      () async {
    final wishlist = WishlistModel(MockWishlistRepository(network));
    await wishlist.load();
    final before = wishlist.items.length;

    final error = await wishlist.add(const WishlistItem(0, 3, 2, 5000));
    expect(error, isNull);
    expect(wishlist.items.length, before + 1);
    final created = wishlist.byProduct(3)!;
    expect(created.id, greaterThanOrEqualTo(1000));

    expect(await wishlist.remove(created.id), isNull);
    expect(wishlist.byProduct(3), isNull);
  });

  test('WishlistModel: при аварии add возвращает ошибку, список не меняется',
      () async {
    final wishlist = WishlistModel(MockWishlistRepository(network));
    await wishlist.load();
    final before = wishlist.items.length;

    network.simulateError = true;
    final error = await wishlist.add(const WishlistItem(0, 3, 2, 5000));
    expect(error, MockNetwork.errorMessage);
    expect(wishlist.items.length, before);
  });
}
