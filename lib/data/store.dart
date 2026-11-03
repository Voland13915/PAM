// data/store.dart — доменная модель магазина.

/// Интернет-магазин, цены которого отслеживает приложение.
class Store {
  final int id;
  final String name;
  final String website;
  final int productsTracked; // сколько товаров магазина есть в базе
  final String lastSync; // когда цены обновлялись последний раз

  const Store(this.id, this.name, this.website, this.productsTracked,
      this.lastSync);
}
