import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tech_price/data/product.dart';
import 'package:tech_price/models/app_settings.dart';
import 'package:tech_price/models/savings_report.dart';
import 'package:tech_price/utils/formatters.dart';

Product item(int id, List<Offer> offers, {String category = 'Смартфоны'}) =>
    Product(
      id: id,
      name: 'Товар $id',
      brand: 'Brand',
      category: category,
      specs: const {},
      offers: offers,
      priceHistory: const [],
    );

void main() {
  final report = SavingsReport.of([
    item(1, const [Offer(1, 1000), Offer(2, 1300), Offer(3, 1600)]),
    item(2, const [Offer(2, 500, oldPrice: 600), Offer(1, 700)],
        category: 'Телевизоры'),
    item(3, const [Offer(3, 200)], category: 'Телевизоры'),
    item(4, const [Offer(1, 900, inStock: false)]),
    item(5, const [Offer(1, 100), Offer(2, 80, inStock: false)]),
  ]);

  test('итоги по лучшим, средним и самым высоким ценам', () {
    expect(report.items.length, 4);
    expect(report.unavailable.map((p) => p.id), [4]);
    expect(report.bestTotal, 1000 + 500 + 200 + 100);
    expect(report.highestTotal, 1600 + 700 + 200 + 100);
    expect(report.averageTotal, 1300 + 600 + 200 + 100);
    expect(report.saving(SavingsBaseline.highest), 800);
    expect(report.saving(SavingsBaseline.average), 400);
    expect(report.percent(SavingsBaseline.highest), closeTo(800 / 2600 * 100, 1e-9));
  });

  test('товар не в наличии в магазине не участвует в сравнении', () {
    final only = report.items.firstWhere((i) => i.product.id == 5);
    expect(only.comparable, isFalse);
    expect(only.saving(SavingsBaseline.highest), 0);
    expect(report.singleStore, 2);
  });

  test('скидки, магазины и категории', () {
    expect(report.discounts, 100);
    final stores = report.byStore(SavingsBaseline.highest);
    expect(stores.first.storeId, 1);
    expect(stores.first.items.map((i) => i.product.id), [1, 5]);
    expect(stores.first.saving(SavingsBaseline.highest), 600);
    expect(stores.first.total, 1100);
    final categories = report.byCategory(SavingsBaseline.highest);
    expect(categories.map((c) => c.category), ['Смартфоны', 'Телевизоры']);
    expect(categories.last.count, 2);
    expect(categories.last.saving, 200);
    expect(report.ranked(SavingsBaseline.highest).first.product.id, 1);
  });

  test('настройки сохраняются', () async {
    SharedPreferences.setMockInitialValues({});
    final settings = await AppSettings.load();
    expect(settings.notifications, isTrue);
    expect(settings.savingsBaseline, SavingsBaseline.highest);
    await settings.setNotifications(false);
    await settings.setSavingsBaseline(SavingsBaseline.average);
    final again = await AppSettings.load();
    expect(again.notifications, isFalse);
    expect(again.savingsBaseline, SavingsBaseline.average);
    expect(await AppSettings.notificationsAllowed(), isFalse);
  });

  test('склонения и размеры', () {
    expect(itemsWord(1), 'товар');
    expect(itemsWord(3), 'товара');
    expect(itemsWord(11), 'товаров');
    expect(itemsWord(22), 'товара');
    expect(formatBytes(512), '512 Б');
    expect(formatBytes(2048), '2 КБ');
    expect(formatBytes(1572864), '1,5 МБ');
  });
}
