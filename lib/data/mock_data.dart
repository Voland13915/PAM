import 'dart:math';

class Store {
  final int id;
  final String name;
  final String website;
  final int productsTracked;
  final String lastSync;

  const Store(this.id, this.name, this.website, this.productsTracked,
      this.lastSync);
}

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

  List<Offer> get inStockOffers => offers.where((o) => o.inStock).toList();

  Offer get bestOffer =>
      inStockOffers.reduce((a, b) => a.price <= b.price ? a : b);

  double get maxPrice => inStockOffers.map((o) => o.price).reduce(max);

  double get priceSpread => maxPrice - bestOffer.price;
}

class WishlistItem {
  final int productId;
  final double targetPrice;

  const WishlistItem(this.productId, this.targetPrice);
}

class UserProfile {
  final String name;
  final String email;
  final String city;
  final double savedTotal;

  const UserProfile(this.name, this.email, this.city, this.savedTotal);
}

// ---------------------------------------------------------------------------

const mockStores = [
  Store(1, 'Bomba', 'bomba.md', 1240, '12 мин назад'),
  Store(2, 'Maximum', 'maximum.md', 1185, '15 мин назад'),
  Store(3, 'Darwin', 'darwin.md', 860, '20 мин назад'),
  Store(4, 'Enter', 'enter.online', 930, '25 мин назад'),
  Store(5, 'Smart', 'smart.md', 715, '40 мин назад'),
  Store(6, 'Ultra', 'ultra.md', 1020, '1 ч назад'),
];

const mockCategories = [
  'Смартфоны',
  'Ноутбуки',
  'Телевизоры',
  'Наушники',
  'Стиральные машины',
  'Холодильники',
  'Пылесосы',
  'Микроволновки',
];

const mockProducts = [
  Product(
    id: 1,
    name: 'Samsung Galaxy A36 5G 8/256GB',
    brand: 'Samsung',
    category: 'Смартфоны',
    specs: {
      'Экран': '6.7", Super AMOLED, 120 Гц',
      'Процессор': 'Snapdragon 6 Gen 3',
      'Память': '8 / 256 ГБ',
      'Камера': '50 + 8 + 5 Мп',
      'Аккумулятор': '5000 мАч',
    },
    offers: [
      Offer(1, 6999),
      Offer(2, 6849),
      Offer(3, 7199),
      Offer(4, 6899, oldPrice: 7299),
      Offer(5, 7049),
    ],
    priceHistory: [7499, 7399, 7299, 7199, 6999, 6849],
  ),
  Product(
    id: 2,
    name: 'Apple iPhone 16 128GB',
    brand: 'Apple',
    category: 'Смартфоны',
    specs: {
      'Экран': '6.1", OLED',
      'Процессор': 'Apple A18',
      'Память': '128 ГБ',
      'Камера': '48 + 12 Мп',
    },
    offers: [
      Offer(3, 16999),
      Offer(4, 16799),
      Offer(5, 16899),
      Offer(1, 17499),
      Offer(6, 16649, inStock: false),
    ],
    priceHistory: [18499, 17999, 17799, 17499, 16999, 16799],
  ),
  Product(
    id: 3,
    name: 'Xiaomi Redmi Note 14 Pro 5G 8/256GB',
    brand: 'Xiaomi',
    category: 'Смартфоны',
    specs: {
      'Экран': '6.67", AMOLED, 120 Гц',
      'Процессор': 'Dimensity 7300-Ultra',
      'Память': '8 / 256 ГБ',
      'Камера': '200 + 8 + 2 Мп',
      'Аккумулятор': '5110 мАч',
    },
    offers: [
      Offer(1, 5299),
      Offer(2, 5199),
      Offer(3, 5399),
      Offer(5, 5249, oldPrice: 5699),
    ],
    priceHistory: [5999, 5799, 5699, 5499, 5299, 5199],
  ),
  Product(
    id: 4,
    name: 'Lenovo IdeaPad Slim 3 15IRH8 i5/16GB/512GB',
    brand: 'Lenovo',
    category: 'Ноутбуки',
    specs: {
      'Экран': '15.6", FHD IPS',
      'Процессор': 'Intel Core i5-13420H',
      'ОЗУ': '16 ГБ',
      'Накопитель': 'SSD 512 ГБ',
      'Вес': '1.62 кг',
    },
    offers: [
      Offer(2, 11999),
      Offer(3, 12499),
      Offer(4, 11799, oldPrice: 12999),
      Offer(6, 12199),
    ],
    priceHistory: [12999, 12999, 12699, 12499, 11999, 11799],
  ),
  Product(
    id: 5,
    name: 'Samsung UE55DU7100 55" 4K Smart TV',
    brand: 'Samsung',
    category: 'Телевизоры',
    specs: {
      'Диагональ': '55"',
      'Разрешение': '3840 × 2160 (4K)',
      'Smart TV': 'Tizen',
      'HDR': 'HDR10+',
    },
    offers: [
      Offer(1, 8999),
      Offer(2, 8799),
      Offer(6, 9199),
      Offer(5, 8899),
    ],
    priceHistory: [9999, 9799, 9499, 9299, 8999, 8799],
  ),
  Product(
    id: 6,
    name: 'Sony WH-1000XM5',
    brand: 'Sony',
    category: 'Наушники',
    specs: {
      'Тип': 'Накладные, беспроводные',
      'Шумоподавление': 'Активное',
      'Работа от батареи': 'до 30 ч',
      'Bluetooth': '5.2',
    },
    offers: [
      Offer(3, 5499),
      Offer(4, 5299),
      Offer(5, 5399),
      Offer(1, 5699),
    ],
    priceHistory: [5999, 5899, 5799, 5599, 5499, 5299],
  ),
  Product(
    id: 7,
    name: 'LG F2WR509SBW 9 кг',
    brand: 'LG',
    category: 'Стиральные машины',
    specs: {
      'Загрузка': '9 кг',
      'Отжим': '1200 об/мин',
      'Класс энергопотребления': 'A',
      'Двигатель': 'Инверторный, прямой привод',
    },
    offers: [
      Offer(1, 8499),
      Offer(2, 8299, oldPrice: 8999),
      Offer(6, 8699),
    ],
    priceHistory: [8999, 8999, 8799, 8699, 8499, 8299],
  ),
  Product(
    id: 8,
    name: 'Bosch KGN39VLCT No Frost 203 см',
    brand: 'Bosch',
    category: 'Холодильники',
    specs: {
      'Высота': '203 см',
      'Общий объём': '363 л',
      'Система': 'No Frost',
      'Класс энергопотребления': 'C',
    },
    offers: [
      Offer(1, 12999),
      Offer(2, 13299),
      Offer(6, 12799),
    ],
    priceHistory: [13999, 13799, 13499, 13299, 12999, 12799],
  ),
  Product(
    id: 9,
    name: 'Xiaomi Robot Vacuum S20',
    brand: 'Xiaomi',
    category: 'Пылесосы',
    specs: {
      'Тип': 'Робот-пылесос',
      'Уборка': 'Сухая и влажная',
      'Мощность всасывания': '5000 Па',
      'Навигация': 'Лазерная (LDS)',
    },
    offers: [
      Offer(3, 3999),
      Offer(5, 3799),
      Offer(4, 3899),
      Offer(2, 4099),
    ],
    priceHistory: [4499, 4399, 4299, 4099, 3999, 3799],
  ),
  Product(
    id: 10,
    name: 'Samsung MS23K3614AW 23 л',
    brand: 'Samsung',
    category: 'Микроволновки',
    specs: {
      'Объём': '23 л',
      'Мощность': '800 Вт',
      'Управление': 'Сенсорное',
    },
    offers: [
      Offer(1, 1599),
      Offer(2, 1549),
      Offer(6, 1649),
    ],
    priceHistory: [1799, 1749, 1699, 1649, 1599, 1549],
  ),
];

const mockWishlist = [
  WishlistItem(1, 6800),
  WishlistItem(2, 16000),
  WishlistItem(4, 11500),
  WishlistItem(6, 5000),
  WishlistItem(7, 8500),
  WishlistItem(8, 12500),
  WishlistItem(9, 3900),
];

const mockShoppingListIds = [1, 5, 6, 7, 9, 10];

const mockUser = UserProfile(
  'Ион Попеску',
  'ion.popescu@mail.md',
  'Кишинёв',
  2340,
);

Product productById(int id) => mockProducts.firstWhere((p) => p.id == id);
Store storeById(int id) => mockStores.firstWhere((s) => s.id == id);
