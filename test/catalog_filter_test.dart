import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/data/catalog_filter.dart';
import 'package:tech_price/models/catalog_model.dart';

import 'fakes.dart';

void main() {
  test('CatalogFilter: параметры запроса только для заданных полей', () {
    expect(const CatalogFilter().toQuery(), isEmpty);

    const filter = CatalogFilter(
      category: 'Смартфоны',
      brands: {'Apple', 'Samsung'},
      storeId: 2,
      minPrice: 5000,
      maxPrice: 15000.4,
      onlyDiscount: true,
      onlyMultiStore: true,
      includeUnavailable: true,
      sort: CatalogSort.priceAsc,
    );
    expect(filter.toQuery(), {
      'category': 'Смартфоны',
      'brand': 'Apple,Samsung',
      'store': '2',
      'min_price': '5000',
      'max_price': '15000',
      'discount': '1',
      'multi': '1',
      'unavailable': '1',
      'sort': 'price_asc',
    });
    expect(filter.activeCount, 7);
  });

  test('CatalogFilter: copyWith умеет сбрасывать значения в null', () {
    const filter = CatalogFilter(storeId: 1, minPrice: 100, maxPrice: 200);
    final cleared = filter.copyWith(storeId: () => null, minPrice: () => null);
    expect(cleared.storeId, isNull);
    expect(cleared.minPrice, isNull);
    expect(cleared.maxPrice, 200);
    expect(filter.copyWith().storeId, 1);
  });

  test('cleared оставляет категорию и сортировку', () {
    const filter = CatalogFilter(
      category: 'Ноутбуки',
      brands: {'ASUS'},
      onlyDiscount: true,
      sort: CatalogSort.discount,
    );
    final cleared = filter.cleared();
    expect(cleared.category, 'Ноутбуки');
    expect(cleared.sort, CatalogSort.discount);
    expect(cleared.activeCount, 0);
  });

  test('CatalogModel.applyFilter перезагружает каталог с фильтром', () async {
    final repository = FakeProductRepository([
      product(1, category: 'Смартфоны'),
      product(2, category: 'Ноутбуки'),
      product(3, category: 'Ноутбуки'),
    ]);
    final catalog = CatalogModel(repository, FakeStoreRepository());
    await catalog.load();
    expect(catalog.products.length, 3);
    expect(catalog.categories.toSet(), {'Смартфоны', 'Ноутбуки'});

    await catalog.applyFilter(const CatalogFilter(category: 'Ноутбуки'));
    expect(catalog.products.map((p) => p.id), [2, 3]);
    expect(catalog.facets.total, 2);
    expect(catalog.facets.categoriesTotal, 3);
    expect(repository.lastFilter.category, 'Ноутбуки');
  });

  test('CatalogModel.images кэширует галерею и не кэширует ошибку', () async {
    final repository = FakeProductRepository([product(1)])
      ..images[1] = ['https://a/1.webp', 'https://a/2.webp'];
    final catalog = CatalogModel(repository, FakeStoreRepository());

    expect(await catalog.images(1), hasLength(2));
    expect(await catalog.images(1), hasLength(2));
    expect(repository.imageRequests, 1);

    repository.fail = true;
    expect(await catalog.images(2), isEmpty);
    repository.fail = false;
    expect(await catalog.images(2), isEmpty);
    expect(repository.imageRequests, 3);
  });

  test('Фото каждого цвета кэшируются отдельно', () async {
    final repository = FakeProductRepository([product(1)])
      ..images[1] = ['https://a/1.webp'];
    final catalog = CatalogModel(repository, FakeStoreRepository());

    await catalog.images(1, color: 'black');
    await catalog.images(1, color: 'black');
    await catalog.images(1, color: 'silver');
    await catalog.images(1);
    expect(repository.imageColors, ['black', 'silver', '']);
  });
}
