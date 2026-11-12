import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/models/catalog_model.dart';

import 'fakes.dart';

void main() {
  test('первая страница — 20 товаров, хвост просит ещё', () async {
    final repository =
        FakeProductRepository([for (var i = 1; i <= 24; i++) product(i)]);
    final catalog = CatalogModel(repository, FakeStoreRepository());

    await catalog.load();
    expect(catalog.products.length, 20);
    expect(catalog.hasMore, isTrue);

    await catalog.loadMore();
    expect(catalog.products.length, 24);
    expect(catalog.hasMore, isFalse);
    expect(repository.requestedPages, [1, 2]);
  });

  test('повторный loadMore во время загрузки не дублирует страницу', () async {
    final repository =
        FakeProductRepository([for (var i = 1; i <= 45; i++) product(i)]);
    final catalog = CatalogModel(repository, FakeStoreRepository());
    await catalog.load();

    final first = catalog.loadMore();
    final second = catalog.loadMore();
    await Future.wait([first, second]);
    expect(catalog.products.length, 40);
    expect(repository.requestedPages, [1, 2]);
  });

  test('поиск идёт через хранилище, retry сохраняет фильтр', () async {
    final repository = FakeProductRepository([
      product(1, name: 'Samsung'),
      product(2, name: 'Apple'),
    ]);
    final catalog = CatalogModel(repository, FakeStoreRepository());

    await catalog.load(search: 'apple');
    expect(catalog.products.single.id, 2);

    await catalog.load();
    expect(catalog.search, 'apple');
    expect(catalog.products.single.id, 2);
  });

  test('byId спрашивает товар, которого нет на загруженной странице',
      () async {
    final repository =
        FakeProductRepository([for (var i = 1; i <= 24; i++) product(i)]);
    final catalog = CatalogModel(repository, FakeStoreRepository());
    await catalog.load();

    expect(catalog.byId(23), isNull);
    expect(catalog.isResolving, isTrue);
    await Future<void>.delayed(Duration.zero);
    expect(catalog.byId(23)?.id, 23);
    expect(catalog.isResolving, isFalse);
  });
}
