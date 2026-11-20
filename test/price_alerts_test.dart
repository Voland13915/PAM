import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tech_price/data/product.dart';
import 'package:tech_price/data/wishlist_item.dart';
import 'package:tech_price/services/price_alerts.dart';

Product _phone(List<Offer> offers) => Product(
      id: 5,
      name: 'Apple iPhone 17 Pro 256GB',
      brand: 'Apple',
      category: 'Смартфоны',
      specs: const {},
      offers: offers,
      priceHistory: const [],
    );

void main() {
  const item = WishlistItem(1, 5, 2, 26000);

  test('Уведомление, когда цена дошла до целевой', () {
    final alerts = findAlerts(
      [item],
      {5: _phone(const [Offer(1, 27000), Offer(2, 25900)])},
      {},
    );
    expect(alerts, hasLength(1));
    expect(alerts.single.offer.price, 25900);
  });

  test('Без уведомления: дорого, нет в наличии или слежение выключено', () {
    expect(findAlerts([item], {5: _phone(const [Offer(1, 26500)])}, {}),
        isEmpty);
    expect(
        findAlerts(
            [item], {5: _phone(const [Offer(1, 25000, inStock: false)])}, {}),
        isEmpty);
    expect(
        findAlerts([item.copyWith(notify: false)],
            {5: _phone(const [Offer(1, 25000)])}, {}),
        isEmpty);
    expect(findAlerts([item], {}, {}), isEmpty);
  });

  test('Повторно уведомляет только о дальнейшем снижении', () {
    final cheap = {5: _phone(const [Offer(1, 25900)])};
    expect(findAlerts([item], cheap, {1: 25900}), isEmpty);
    final cheaper = {5: _phone(const [Offer(1, 25500)])};
    expect(findAlerts([item], cheaper, {1: 25900}), hasLength(1));
  });

  test('Память сбрасывается, когда цена снова выше целевой', () {
    final sent = findAlerts([item], {5: _phone(const [Offer(1, 25900)])}, {});
    final remembered = rememberAlerts(
        [item], {5: _phone(const [Offer(1, 25900)])}, {}, sent);
    expect(remembered, {1: 25900});

    final up = rememberAlerts(
        [item], {5: _phone(const [Offer(1, 27000)])}, remembered, const []);
    expect(up, isEmpty);

    final unknown = rememberAlerts([item], {}, remembered, const []);
    expect(unknown, {1: 25900});
  });

  test('Отправленные цены сохраняются между запусками', () async {
    SharedPreferences.setMockInitialValues({});
    final memory = NotifiedPrices();
    await memory.save({1: 25900, 7: 999.5});
    expect(await memory.load(), {1: 25900.0, 7: 999.5});
  });
}
