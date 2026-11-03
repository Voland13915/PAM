// data/product.dart — доменная модель товара. Переживает L5:
// mock умрёт, а этот файл импортирует кто угодно.
import 'dart:math';

/// Предложение: цена товара в конкретном магазине.
class Offer {
  final int storeId;
  final double price;
  final double? oldPrice; // цена до скидки, если есть
  final bool inStock;

  const Offer(this.storeId, this.price, {this.oldPrice, this.inStock = true});
}

/// Товар с ценами во всех магазинах — главная сущность темы.
class Product {
  final int id; // идентичность: путешествует в адресе /catalog/:id
  final String name;
  final String brand;
  final String category;
  final Map<String, String> specs;
  final List<Offer> offers;
  final List<double> priceHistory; // минимальная цена за 6 месяцев

  const Product({
    required this.id,
    required this.name,
    required this.brand,
    required this.category,
    required this.specs,
    required this.offers,
    required this.priceHistory,
  });

  /// «Тот же товар, другая идентичность» — для create: id даёт хранилище.
  Product copyWith({int? id}) => Product(
        id: id ?? this.id,
        name: name,
        brand: brand,
        category: category,
        specs: specs,
        offers: offers,
        priceHistory: priceHistory,
      );

  List<Offer> get inStockOffers => offers.where((o) => o.inStock).toList();

  /// Самое дешёвое предложение среди магазинов, где товар в наличии.
  Offer get bestOffer =>
      inStockOffers.reduce((a, b) => a.price <= b.price ? a : b);

  double get maxPrice => inStockOffers.map((o) => o.price).reduce(max);

  /// Разница между самой высокой и самой низкой ценой.
  double get priceSpread => maxPrice - bestOffer.price;
}
