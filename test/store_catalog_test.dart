import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/data/catalog_filter.dart';
import 'package:tech_price/models/catalog_model.dart';

import 'fakes.dart';

void main() {
  test('каталог магазина всегда запрашивает свой магазин', () async {
    final repository = FakeProductRepository([product(1), product(2)]);
    final catalog =
        CatalogModel(repository, FakeStoreRepository(), storeId: 2);

    await catalog.load();
    expect(repository.lastFilter.storeId, 2);
    expect(catalog.activeFilters, 0);

    await catalog.applyFilter(const CatalogFilter(onlyDiscount: true));
    expect(repository.lastFilter.storeId, 2);
    expect(repository.lastFilter.onlyDiscount, isTrue);
    expect(catalog.activeFilters, 1);

    await catalog.applyFilter(const CatalogFilter());
    expect(repository.lastFilter.storeId, 2);
    expect(catalog.activeFilters, 0);
  });

  test('общий каталог не привязан к магазину', () async {
    final repository = FakeProductRepository([product(1)]);
    final catalog = CatalogModel(repository, FakeStoreRepository());

    await catalog.load();
    expect(repository.lastFilter.storeId, isNull);

    await catalog.applyFilter(const CatalogFilter(storeId: 3));
    expect(repository.lastFilter.storeId, 3);
    expect(catalog.activeFilters, 1);
  });
}
