import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'data/api_client.dart';
import 'data/auth_api.dart';
import 'data/auth_user.dart';
import 'data/http_product_repository.dart';
import 'data/http_store_repository.dart';
import 'data/http_wishlist_repository.dart';
import 'data/result.dart';
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
  final api = ApiClient(apiBase, tokens);
  final auth = AuthApi(api, tokens);

  final user = await _currentUser(tokens, auth);
  final loggedIn = await tokens.read() != null;

  router = createRouter(loggedIn ? '/catalog' : '/login');
  api.onUnauthorized = () => router.go('/login');

  final productRepository = HttpProductRepository(api);
  final storeRepository = HttpStoreRepository(api);
  final wishlistRepository = HttpWishlistRepository(api);

  runApp(
    MultiProvider(
      providers: [
        Provider<AuthApi>.value(value: auth),
        ChangeNotifierProvider(
          create: (_) => CatalogModel(productRepository, storeRepository)
            ..load(), // DI — как на L4
        ),
        ChangeNotifierProvider(
          create: (_) => WishlistModel(wishlistRepository)..load(),
        ),
        ChangeNotifierProvider(create: (_) => ShoppingListModel()),
        ChangeNotifierProvider(create: (_) {
          final session = SessionModel();
          if (user != null) session.register(user.name, user.email);
          return session;
        }),
      ],
      child: const MyApp(),
    ),
  );
}

Future<AuthUser?> _currentUser(TokenStore tokens, AuthApi auth) async {
  if (await tokens.read() == null) return null;
  return switch (await auth.me()) {
    Ok(:final value) => value,
    Err() => null,
  };
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
