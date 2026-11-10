import 'dart:math';

class Offer {
  final int storeId;
  final double price;
  final double? oldPrice;
  final bool inStock;

  const Offer(this.storeId, this.price, {this.oldPrice, this.inStock = true});
}

class Product {
  final int id;
  final String name;
  final String brand;
  final String category;
  final Map<String, String> specs;
  final List<Offer> offers;
  final List<double> priceHistory;

  const Product({
    required this.id,
    required this.name,
    required this.brand,
    required this.category,
    required this.specs,
    required this.offers,
    required this.priceHistory,
  });

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

  Offer get bestOffer =>
      inStockOffers.reduce((a, b) => a.price <= b.price ? a : b);

  double get maxPrice => inStockOffers.map((o) => o.price).reduce(max);

  double get priceSpread => maxPrice - bestOffer.price;
}
