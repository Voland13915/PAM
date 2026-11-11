import 'dart:math';

class Offer {
  final int storeId;
  final double price;
  final double? oldPrice;
  final bool inStock;

  const Offer(this.storeId, this.price, {this.oldPrice, this.inStock = true});

  factory Offer.fromJson(Map<String, dynamic> j) => Offer(
        j['storeId'] as int,
        (j['price'] as num).toDouble(),
        oldPrice: (j['oldPrice'] as num?)?.toDouble(),
        inStock: j['inStock'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'storeId': storeId,
        'price': price,
        'oldPrice': oldPrice,
        'inStock': inStock,
      };
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

  factory Product.fromJson(Map<String, dynamic> j) => Product(
        id: j['id'] as int,
        name: j['name'] as String,
        brand: j['brand'] as String? ?? '',
        category: j['category'] as String,
        specs: (j['specs'] as Map<String, dynamic>? ?? const {})
            .map((key, value) => MapEntry(key, value as String)),
        offers: (j['offers'] as List)
            .map((e) => Offer.fromJson(e as Map<String, dynamic>))
            .toList(),
        priceHistory: (j['priceHistory'] as List? ?? const [])
            .map((e) => (e as num).toDouble())
            .toList(),
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'brand': brand,
        'category': category,
        'specs': specs,
        'offers': [for (final o in offers) o.toJson()],
        'priceHistory': priceHistory,
      };

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
