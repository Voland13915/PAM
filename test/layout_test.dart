import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tech_price/data/offline_status.dart';
import 'package:tech_price/data/product.dart';
import 'package:tech_price/data/product_repository.dart';
import 'package:tech_price/data/response_cache.dart';
import 'package:tech_price/data/result.dart';
import 'package:tech_price/data/store.dart';
import 'package:tech_price/data/store_repository.dart';
import 'package:tech_price/data/wishlist_item.dart';
import 'package:tech_price/main.dart';
import 'package:tech_price/models/app_settings.dart';
import 'package:tech_price/models/catalog_model.dart';
import 'package:tech_price/models/session_model.dart';
import 'package:tech_price/models/shopping_list_model.dart';
import 'package:tech_price/models/wishlist_model.dart';
import 'package:tech_price/router.dart';

import 'fakes.dart';

class _Screen {
  final String name;
  final Size size;

  const _Screen(this.name, this.size);
}

const _screens = [
  _Screen('маленький 320×568', Size(320, 568)),
  _Screen('обычный 360×800', Size(360, 800)),
  _Screen('альбомный 800×360', Size(800, 360)),
  _Screen('планшет 800×1280', Size(800, 1280)),
];

const _textScales = [1.0, 1.3, 2.0];

const _locations = [
  '/catalog',
  '/catalog/1',
  '/wishlist',
  '/shopping',
  '/profile',
  '/profile/savings',
  '/profile/stores',
  '/profile/stores/6',
];

class _Stores extends FakeStoreRepository {
  @override
  Future<Result<List<Store>>> fetchAll() async => const Ok([
        Store(1, 'Maximum', 'maximum.md', 12840, ''),
        Store(2, 'Ultra', 'ultra.md', 9311, ''),
        Store(3, 'Smart', 'smart.md', 4120, ''),
        Store(4, 'Cactus', 'cactus.md', 7302, ''),
        Store(5, 'XStore', 'xstore.md', 2210, ''),
        Store(6, 'Darwin', 'darwin.md', 10544, ''),
        Store(7, 'Enter', 'enter.md', 8876, ''),
        Store(8, 'PandaShop', 'pandashop.md', 15032, ''),
      ]);
}

final _dates = [
  for (var i = 0; i < 10; i++) DateTime(2026, 9, 1).add(Duration(days: i * 8)),
];

final _products = [
  Product(
    id: 1,
    name: 'Samsung Galaxy S25 Ultra 12/512GB Titanium Silverblue SM-S938B',
    brand: 'Samsung',
    category: 'Смартфоны',
    specs: const {
      'Экран': '6.9″ Dynamic AMOLED 2X, 3120×1440, 120 Гц',
      'Процессор': 'Snapdragon 8 Elite for Galaxy',
      'Память': '12 ГБ / 512 ГБ',
      'Камера': '200 + 50 + 50 + 10 Мп',
      'Аккумулятор': '5000 мАч, 45 Вт',
      'Цвет': 'Titanium Silverblue',
    },
    offers: const [
      Offer(1, 23999, oldPrice: 27999),
      Offer(2, 24499),
      Offer(4, 25999),
      Offer(6, 22899, oldPrice: 26499),
      Offer(8, 27499, inStock: false),
    ],
    priceHistory: const [
      27999, 27499, 26999, 26499, 25999, 25499, 24999, 23999, 23499, 22899,
    ],
    priceHistoryDates: _dates,
    colors: const [
      ProductColor(code: 'blue', name: 'Titanium Silverblue', hex: '#9FB4C7'),
      ProductColor(code: 'black', name: 'Titanium Black', hex: '#2B2B2B'),
      ProductColor(code: 'gray', name: 'Titanium Gray', hex: '#8A8A8A'),
      ProductColor(code: 'white', name: 'Titanium Whitesilver', hex: '#EDEDED'),
      ProductColor(code: 'green', name: 'Titanium Jadegreen', hex: '#5E8C76'),
      ProductColor(code: 'pink', name: 'Titanium Pinkgold', hex: '#E6C1B5'),
      ProductColor(code: 'jet', name: 'Titanium Jetblack', hex: '#111111'),
    ],
  ),
  Product(
    id: 2,
    name: 'LG OLED evo C4 65" 4K Smart TV webOS OLED65C46LA',
    brand: 'LG',
    category: 'Телевизоры',
    specs: const {'Диагональ': '65″', 'Разрешение': '3840×2160'},
    offers: const [Offer(2, 41999), Offer(6, 39999), Offer(7, 44999)],
    priceHistory: const [44999, 42999, 39999],
  ),
  Product(
    id: 3,
    name: 'Стиральная машина Bosch Serie 6 WGG254ZMBY 10 кг 1400 об/мин',
    brand: 'Bosch',
    category: 'Стиральные машины',
    specs: const {'Загрузка': '10 кг'},
    offers: const [Offer(4, 13499)],
    priceHistory: const [13499],
  ),
  Product(
    id: 4,
    name: 'Пылесос Dyson V15 Detect Absolute',
    brand: 'Dyson',
    category: 'Пылесосы',
    specs: const {},
    offers: const [Offer(3, 15999, inStock: false)],
    priceHistory: const [15999],
  ),
  Product(
    id: 5,
    name: 'Микроволновая печь Samsung MS23K3513AW',
    brand: 'Samsung',
    category: 'Микроволновки',
    specs: const {},
    offers: const [Offer(1, 1499, oldPrice: 1799), Offer(8, 1699)],
    priceHistory: const [1799, 1499],
  ),
];

late AppSettings _settings;

Future<Widget> _app() async {
  final products = FakeProductRepository(_products);
  final stores = _Stores();
  final wishlistRepository = FakeWishlistRepository();
  await wishlistRepository.create(const WishlistItem(0, 1, 6, 21999));
  await wishlistRepository.create(const WishlistItem(0, 2, 6, 40999));
  await wishlistRepository.create(
      const WishlistItem(0, 5, 1, 1299, notify: false));
  final catalog = CatalogModel(products, stores);
  await catalog.load();
  final wishlist = WishlistModel(wishlistRepository);
  await wishlist.load();
  final shopping = ShoppingListModel();
  for (final p in _products) {
    shopping.add(p.id);
  }
  final session = SessionModel()
    ..register('Мигов Даниил Александрович', 'daniil.migov.ti237@utm.example.md');
  final cache = ResponseCache(
    directory: () async =>
        Directory('${Directory.systemTemp.path}/techprice_layout_cache'),
  );

  return MultiProvider(
    providers: [
      Provider<ResponseCache>.value(value: cache),
      Provider<ProductRepository>.value(value: products),
      Provider<StoreRepository>.value(value: stores),
      ChangeNotifierProvider(create: (_) => OfflineStatus()),
      ChangeNotifierProvider<AppSettings>.value(value: _settings),
      ChangeNotifierProvider<CatalogModel>.value(value: catalog),
      ChangeNotifierProvider<WishlistModel>.value(value: wishlist),
      ChangeNotifierProvider<ShoppingListModel>.value(value: shopping),
      ChangeNotifierProvider<SessionModel>.value(value: session),
    ],
    child: const MyApp(),
  );
}

String _describe(FlutterErrorDetails details) {
  final first = details.exceptionAsString().split('\n').first.trim();
  String text;
  try {
    text = details.toString();
  } catch (_) {
    text = '';
  }
  final where = RegExp(
          r'lib/(?:screens|widgets|models|data|utils|services)/\w+\.dart:\d+:\d+')
      .firstMatch(text)
      ?.group(0);
  return where == null ? first : '$first ($where)';
}

Future<void> _settle(WidgetTester tester) async {
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 200));
  }
}

Future<void> _scrollAll(WidgetTester tester) async {
  final states = tester
      .stateList<ScrollableState>(find.byType(Scrollable))
      .where((s) => s.position.axis == Axis.vertical)
      .toList();
  for (final state in states) {
    if (!state.mounted) continue;
    final position = state.position;
    for (var i = 0; i < 60 && position.pixels < position.maxScrollExtent; i++) {
      position.jumpTo(math.min(
        position.pixels + position.viewportDimension * 0.8,
        position.maxScrollExtent,
      ));
      await tester.pump();
    }
    if (state.mounted && position.pixels > 0) {
      position.jumpTo(0);
      await tester.pump();
    }
  }
}

Future<void> _close(WidgetTester tester, Type type) async {
  final found = find.byType(type);
  if (found.evaluate().isEmpty) return;
  Navigator.of(tester.element(found.first)).pop();
  await _settle(tester);
}

void main() {
  setUpAll(() => router = createRouter('/catalog'));

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    _settings = await AppSettings.load();
  });

  for (final screen in _screens) {
    for (final scale in _textScales) {
      final config = '${screen.name}, шрифт ×$scale';
      testWidgets('вёрстка без переполнений: $config', (tester) async {
        tester.view.physicalSize = screen.size;
        tester.view.devicePixelRatio = 1;
        tester.platformDispatcher.textScaleFactorTestValue = scale;
        addTearDown(tester.view.reset);
        addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);

        final problems = <String>[];
        var label = 'запуск';
        final previous = FlutterError.onError;
        FlutterError.onError = (details) {
          final line = '$label — ${_describe(details)}';
          if (!problems.contains(line)) problems.add(line);
        };

        Future<void> step(String name, Future<void> Function() action) async {
          label = name;
          try {
            await action();
            await _settle(tester);
            await _scrollAll(tester);
          } catch (error) {
            problems.add('$name — не удалось проверить: $error');
          }
        }

        Future<void> dialog(String name, String tile) => step(name, () async {
              router.go('/profile');
              await _settle(tester);
              final target = find.text(tile);
              await tester.scrollUntilVisible(target, 200,
                  scrollable: find.byType(Scrollable).first);
              await tester.tap(target);
              await _settle(tester);
              await _scrollAll(tester);
              await _close(tester, AlertDialog);
            });

        Future<void> sheet(String name, Finder button) => step(name, () async {
              router.go('/catalog');
              await _settle(tester);
              await tester.tap(button.first, warnIfMissed: false);
              await _settle(tester);
              await _scrollAll(tester);
              await _close(tester, BottomSheet);
            });

        try {
          final app = await tester.runAsync(_app);
          await tester.pumpWidget(app!);
          await _settle(tester);

          for (final location in _locations) {
            await step(location, () async => router.go(location));
          }
          await sheet('фильтры каталога', find.text('Фильтры'));
          await sheet('сортировка каталога', find.byIcon(Icons.sort));
          await dialog('диалог смены имени', 'Имя');
          await dialog('диалог смены пароля', 'Сменить пароль');

          await _settings.setThemeMode(ThemeMode.dark);
          await step('тёмная тема /profile/savings',
              () async => router.go('/profile/savings'));
          await _settings.setThemeMode(ThemeMode.system);

          label = 'возврат в каталог';
          router.go('/catalog');
          await _settle(tester);
        } finally {
          FlutterError.onError = previous;
        }

        if (problems.isNotEmpty) {
          debugPrint('\n[$config]\n${problems.map((p) => '  • $p').join('\n')}');
        }
        expect(problems, isEmpty, reason: config);
      });
    }
  }
}
