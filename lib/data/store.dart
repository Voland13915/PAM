class Store {
  final int id;
  final String name;
  final String website;
  final int productsTracked;
  final String lastSync;

  const Store(this.id, this.name, this.website, this.productsTracked,
      this.lastSync);

  factory Store.fromJson(Map<String, dynamic> j) => Store(
        j['id'] as int,
        j['name'] as String,
        j['website'] as String? ?? '',
        j['productsTracked'] as int? ?? 0,
        j['lastSync'] as String? ?? '',
      );
}
