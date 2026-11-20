import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/data/product.dart';
import 'package:tech_price/utils/formatters.dart';

const _nbsp = '\u00A0';

void main() {
  test('Product.fromJson читает даты истории и ссылку предложения', () {
    final p = Product.fromJson({
      'id': 1,
      'name': 'Samsung Galaxy A36',
      'brand': 'Samsung',
      'category': 'Смартфоны',
      'specs': <String, dynamic>{},
      'offers': [
        {'storeId': 1, 'price': 6999, 'oldPrice': null, 'inStock': true,
          'url': 'https://bomba.md/ru/product/1'},
      ],
      'priceHistory': [7199, 6999],
      'priceHistoryDates': ['2026-11-01', '2026-11-12'],
      'imageUrl': 'https://cdn.ultra.md/images/1.webp',
    });
    expect(p.priceHistoryDates, [DateTime(2026, 11, 1), DateTime(2026, 11, 12)]);
    expect(p.offers.single.url, 'https://bomba.md/ru/product/1');
    expect(p.imageUrl, 'https://cdn.ultra.md/images/1.webp');
  });

  test('Ответ без новых полей тоже читается', () {
    final p = Product.fromJson({
      'id': 1,
      'name': 'Старый формат',
      'category': 'Смартфоны',
      'offers': [
        {'storeId': 1, 'price': 100},
      ],
    });
    expect(p.priceHistoryDates, isEmpty);
    expect(p.offers.single.url, '');
    expect(p.imageUrl, '');
  });

  test('bestOffer не падает, если товара нет в наличии нигде', () {
    const p = Product(
      id: 1,
      name: 'Закончился',
      brand: '',
      category: 'Смартфоны',
      specs: {},
      offers: [
        Offer(1, 500, inStock: false),
        Offer(2, 450, inStock: false),
      ],
      priceHistory: [],
    );
    expect(p.isAvailable, isFalse);
    expect(p.bestOffer.price, 450);
    expect(p.maxPrice, 500);
  });

  test('formatSyncTime показывает, как давно обновлялся магазин', () {
    final now = DateTime.utc(2026, 11, 15, 12, 0);
    expect(formatSyncTime('', now: now), 'ещё не обновлялся');
    expect(formatSyncTime('2026-11-15T11:59:40.000Z', now: now), 'только что');
    expect(formatSyncTime('2026-11-15T11:48:00.000Z', now: now),
        '12$_nbspмин назад');
    expect(formatSyncTime('2026-11-15T09:00:00.000Z', now: now),
        '3$_nbspч назад');
    expect(formatSyncTime('2026-11-13T12:00:00.000Z', now: now),
        '2$_nbspдн назад');
  });

  test('formatShortDate', () {
    expect(formatShortDate(DateTime(2026, 11, 12)), '12$_nbspноя');
  });

  test('Цвета товара: свои предложения, фото и выбор по умолчанию', () {
    final p = Product.fromJson({
      'id': 7,
      'name': 'Apple iPhone 17 Pro 256GB',
      'category': 'Смартфоны',
      'offers': [
        {'storeId': 1, 'price': 900},
        {'storeId': 2, 'price': 950},
      ],
      'imageUrl': 'https://img/any.jpg',
      'colors': [
        {
          'code': 'black',
          'name': 'Чёрный',
          'hex': '#1d1d1f',
          'imageUrl': 'https://img/black.jpg',
          'offers': [
            {'storeId': 1, 'price': 900},
            {'storeId': 2, 'price': 990},
          ],
        },
        {
          'code': 'silver',
          'name': 'Серебристый',
          'hex': '#d5d6db',
          'offers': [
            {'storeId': 2, 'price': 950, 'inStock': false},
          ],
        },
      ],
    });
    expect(p.colors.map((c) => c.code), ['black', 'silver']);
    expect(p.bestColor?.code, 'black');
    expect(p.colorByCode('silver')?.isAvailable, isFalse);
    expect(p.colorByCode('gold'), isNull);

    final black = p.forColor(p.colors.first);
    expect(black.offers.map((o) => o.price), [900, 990]);
    expect(black.imageUrl, 'https://img/black.jpg');
    expect(black.priceSpread, 90);

    final silver = p.forColor(p.colors.last);
    expect(silver.isAvailable, isFalse);
    expect(silver.imageUrl, 'https://img/any.jpg');
  });
}
