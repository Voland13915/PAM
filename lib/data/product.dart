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

class ProductColor {
  final String code;
  final String name;
  final String hex;
  final String imageUrl;
  final List<Offer> offers;

  const ProductColor({
    required this.code,
    required this.name,
    this.hex = '',
    this.imageUrl = '',
    this.offers = const [],
  });

  factory ProductColor.fromJson(Map<String, dynamic> j) => ProductColor(
        code: j['code'] as String,
        name: j['name'] as String? ?? '',
        hex: j['hex'] as String? ?? '',
        imageUrl: j['imageUrl'] as String? ?? '',
        offers: (j['offers'] as List? ?? const [])
            .map((e) => Offer.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  bool get isAvailable => offers.any((o) => o.inStock);
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
  final String imageUrl;
  final List<ProductColor> colors;

  const Product({
    required this.id,
    required this.name,
    required this.brand,
    required this.category,
    required this.specs,
    required this.offers,
    required this.priceHistory,
    this.priceHistoryDates = const [],
    this.imageUrl = '',
    this.colors = const [],
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
        imageUrl: j['imageUrl'] as String? ?? '',
        colors: (j['colors'] as List? ?? const [])
            .map((e) => ProductColor.fromJson(e as Map<String, dynamic>))
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
        imageUrl: imageUrl,
        colors: colors,
      );

  Product forColor(ProductColor color) => Product(
        id: id,
        name: name,
        brand: brand,
        category: category,
        specs: specs,
        offers: color.offers.isEmpty ? offers : color.offers,
        priceHistory: priceHistory,
        priceHistoryDates: priceHistoryDates,
        imageUrl: color.imageUrl.isEmpty ? imageUrl : color.imageUrl,
        colors: colors,
      );

  ProductColor? colorByCode(String? code) {
    for (final c in colors) {
      if (c.code == code) return c;
    }
    return null;
  }

  ProductColor? get bestColor {
    if (colors.isEmpty || offers.isEmpty) return null;
    final best = bestOffer;
    for (final c in colors) {
      final match = c.offers
          .any((o) => o.storeId == best.storeId && o.price == best.price);
      if (match) return c;
    }
    return null;
  }

  List<Offer> get inStockOffers => offers.where((o) => o.inStock).toList();

  bool get isAvailable => inStockOffers.isNotEmpty;

  List<Offer> get _priced => isAvailable ? inStockOffers : offers;

  Offer get bestOffer => _priced.reduce((a, b) => a.price <= b.price ? a : b);

  double get maxPrice => _priced.map((o) => o.price).reduce(max);

  double get priceSpread => maxPrice - bestOffer.price;
}
