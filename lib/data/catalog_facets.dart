class FacetValue {
  final String name;
  final int count;

  const FacetValue(this.name, this.count);

  factory FacetValue.fromJson(Map<String, dynamic> j) =>
      FacetValue(j['name'] as String, j['count'] as int);
}

class StoreFacet {
  final int id;
  final int count;

  const StoreFacet(this.id, this.count);

  factory StoreFacet.fromJson(Map<String, dynamic> j) =>
      StoreFacet(j['id'] as int, j['count'] as int);
}

class CatalogFacets {
  final List<FacetValue> categories;
  final List<FacetValue> brands;
  final List<StoreFacet> stores;
  final double? minPrice;
  final double? maxPrice;
  final int total;

  const CatalogFacets({
    this.categories = const [],
    this.brands = const [],
    this.stores = const [],
    this.minPrice,
    this.maxPrice,
    this.total = 0,
  });

  static const empty = CatalogFacets();

  factory CatalogFacets.fromJson(Map<String, dynamic> j) => CatalogFacets(
        categories: [
          for (final e in j['categories'] as List? ?? const [])
            FacetValue.fromJson(e as Map<String, dynamic>),
        ],
        brands: [
          for (final e in j['brands'] as List? ?? const [])
            FacetValue.fromJson(e as Map<String, dynamic>),
        ],
        stores: [
          for (final e in j['stores'] as List? ?? const [])
            StoreFacet.fromJson(e as Map<String, dynamic>),
        ],
        minPrice: (j['minPrice'] as num?)?.toDouble(),
        maxPrice: (j['maxPrice'] as num?)?.toDouble(),
        total: j['total'] as int? ?? 0,
      );

  int get categoriesTotal => categories.fold(0, (sum, c) => sum + c.count);

  int storeCount(int id) {
    for (final s in stores) {
      if (s.id == id) return s.count;
    }
    return 0;
  }
}
