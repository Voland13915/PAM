// main.dart — корень композиции: ЗДЕСЬ (и только здесь) выбирается
// источник данных. На L5: http-реализации вместо mock-ов — и всё.
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'data/mock_network.dart';
import 'data/mock_product_repository.dart';
import 'data/mock_store_repository.dart';
import 'data/mock_wishlist_repository.dart';
import 'models/catalog_model.dart';
import 'models/session_model.dart';
import 'models/shopping_list_model.dart';
import 'models/wishlist_model.dart';
import 'router.dart';

void main() {
  final network = MockNetwork(); // задержка + авария для всех mock-ов
  final productRepository = MockProductRepository(network);
  final storeRepository = MockStoreRepository(network);
  final wishlistRepository = MockWishlistRepository(network);

  runApp(
    MultiProvider(
      providers: [
        // Леса демонстрации аварии (переключатель в профиле) — исчезают на L5.
        // Не ChangeNotifier и освобождать нечего, поэтому .value оправдан.
        Provider<MockNetwork>.value(value: network),
        // Модели — фабрикой (C7): Provider создаёт лениво и сам вызывает
        // dispose; каскад ..load() запускает первую загрузку.
        ChangeNotifierProvider(
          create: (_) => CatalogModel(productRepository, storeRepository)
            ..load(),
        ),
        ChangeNotifierProvider(
          create: (_) => WishlistModel(wishlistRepository)..load(),
        ),
        ChangeNotifierProvider(create: (_) => ShoppingListModel()),
        ChangeNotifierProvider(create: (_) => SessionModel()),
      ],
      child: const MyApp(), // MaterialApp.router — нетронут с L3
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'TechPrice',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        // Сине-зелёный: ассоциация с экономией и при этом нейтральный
        // к фирменным цветам магазинов (Bomba, Maximum и др.).
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00796B),
        ),
        textTheme: const TextTheme(
          titleLarge: TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      routerConfig: router,
    );
  }
}
