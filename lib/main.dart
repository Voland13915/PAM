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
        Provider<MockNetwork>.value(value: network),
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
      child: const MyApp(),
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
