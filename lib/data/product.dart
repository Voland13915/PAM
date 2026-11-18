import 'dart:math';

class Offer {
  final int storeId;
  final double price;
  final double? oldPrice;
  final bool inStock;

  final String url;

  const Offer(this.storeId, this.price,
      {this.oldPrice, this.inStock = true, this.url = ''});

  factory Offer.fromJson(Map<String, dynamic> j) => Offer(
        j['storeId'] as int,
        (j['price'] as num).toDouble(),
        oldPrice: (j['oldPrice'] as num?)?.toDouble(),
        inStock: j['inStock'] as bool? ?? true,
        url: j['url'] as String? ?? '',
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

  final List<DateTime> priceHistoryDates;

  const Product({
    required this.id,
    required this.name,
    required this.brand,
    required this.category,
    required this.specs,
    required this.offers,
    required this.priceHistory,
    this.priceHistoryDates = const [],
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
        priceHistoryDates: (j['priceHistoryDates'] as List? ?? const [])
            .map((e) => DateTime.parse(e as String))
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
        priceHistoryDates: priceHistoryDates,
      );

  List<Offer> get inStockOffers => offers.where((o) => o.inStock).toList();

  bool get isAvailable => inStockOffers.isNotEmpty;

  List<Offer> get _priced => isAvailable ? inStockOffers : offers;

  Offer get bestOffer => _priced.reduce((a, b) => a.price <= b.price ? a : b);

  double get maxPrice => _priced.map((o) => o.price).reduce(max);

  double get priceSpread => maxPrice - bestOffer.price;
}
