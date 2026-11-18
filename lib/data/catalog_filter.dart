enum CatalogSort {
  defaultOrder('default', 'Сначала есть в нескольких магазинах'),
  priceAsc('price_asc', 'Сначала дешёвые'),
  priceDesc('price_desc', 'Сначала дорогие'),
  discount('discount', 'По размеру скидки'),
  name('name', 'По названию');

  const CatalogSort(this.apiValue, this.label);

  final String apiValue;
  final String label;
}

class CatalogFilter {
  final String category;
  final Set<String> brands;
  final int? storeId;
  final double? minPrice;
  final double? maxPrice;
  final bool onlyDiscount;
  final bool onlyMultiStore;
  final bool includeUnavailable;
  final CatalogSort sort;

  const CatalogFilter({
    this.category = '',
    this.brands = const {},
    this.storeId,
    this.minPrice,
    this.maxPrice,
    this.onlyDiscount = false,
    this.onlyMultiStore = false,
    this.includeUnavailable = false,
    this.sort = CatalogSort.defaultOrder,
  });

  CatalogFilter copyWith({
    String? category,
    Set<String>? brands,
    int? Function()? storeId,
    double? Function()? minPrice,
    double? Function()? maxPrice,
    bool? onlyDiscount,
    bool? onlyMultiStore,
    bool? includeUnavailable,
    CatalogSort? sort,
  }) =>
      CatalogFilter(
        category: category ?? this.category,
        brands: brands ?? this.brands,
        storeId: storeId != null ? storeId() : this.storeId,
        minPrice: minPrice != null ? minPrice() : this.minPrice,
        maxPrice: maxPrice != null ? maxPrice() : this.maxPrice,
        onlyDiscount: onlyDiscount ?? this.onlyDiscount,
        onlyMultiStore: onlyMultiStore ?? this.onlyMultiStore,
        includeUnavailable: includeUnavailable ?? this.includeUnavailable,
        sort: sort ?? this.sort,
      );

  bool get hasPriceRange => minPrice != null || maxPrice != null;

  int get activeCount =>
      brands.length +
      (storeId != null ? 1 : 0) +
      (hasPriceRange ? 1 : 0) +
      (onlyDiscount ? 1 : 0) +
      (onlyMultiStore ? 1 : 0) +
      (includeUnavailable ? 1 : 0);

  CatalogFilter cleared() => CatalogFilter(category: category, sort: sort);

  Map<String, String> toQuery() => {
        if (category.isNotEmpty) 'category': category,
        if (brands.isNotEmpty) 'brand': brands.join(','),
        if (storeId != null) 'store': '$storeId',
        if (minPrice != null) 'min_price': minPrice!.round().toString(),
        if (maxPrice != null) 'max_price': maxPrice!.round().toString(),
        if (onlyDiscount) 'discount': '1',
        if (onlyMultiStore) 'multi': '1',
        if (includeUnavailable) 'unavailable': '1',
        if (sort != CatalogSort.defaultOrder) 'sort': sort.apiValue,
      };
}
