import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'data/api_client.dart';
import 'data/auth_api.dart';
import 'data/mock_network.dart';
import 'data/mock_product_repository.dart';
import 'data/mock_store_repository.dart';
import 'data/mock_wishlist_repository.dart';
import 'data/token_store.dart';
import 'models/catalog_model.dart';
import 'models/session_model.dart';
import 'models/shopping_list_model.dart';
import 'models/wishlist_model.dart';
import 'router.dart';

const apiBase = String.fromEnvironment(
  'API_BASE',
  defaultValue: 'http://10.0.2.2:8080',
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final tokens = TokenStore();
  final auth = AuthApi(ApiClient(apiBase, tokens), tokens);
  final loggedIn = await tokens.read() != null;
  router = createRouter(loggedIn ? '/catalog' : '/login');

  final network = MockNetwork();
  final productRepository = MockProductRepository(network);
  final storeRepository = MockStoreRepository(network);
  final wishlistRepository = MockWishlistRepository(network);

  runApp(
    MultiProvider(
      providers: [
        Provider<AuthApi>.value(value: auth),
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
