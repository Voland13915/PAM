import 'package:go_router/go_router.dart';

import 'screens/catalog_screen.dart';
import 'screens/login_screen.dart';
import 'screens/product_details_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/register_screen.dart';
import 'screens/shopping_list_screen.dart';
import 'screens/stores_screen.dart';
import 'screens/track_price_screen.dart';
import 'screens/wishlist_screen.dart';
import 'widgets/app_shell.dart';

GoRoute _productRoute(String base) => GoRoute(
      path: ':id',
      builder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return ProductDetailsScreen(productId: id, basePath: base);
      },
      routes: [
        GoRoute(
          path: 'track', // полный адрес: <base>/:id/track
          builder: (context, state) {
            final id = int.parse(state.pathParameters['id']!);
            return TrackPriceScreen(productId: id);
          },
        ),
      ],
    );

final router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/register',
      builder: (context, state) => const RegisterScreen(),
    ),

    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) =>
          AppShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/catalog',
            builder: (context, state) => const CatalogScreen(),
            routes: [_productRoute('/catalog')],
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/wishlist',
            builder: (context, state) => const WishlistScreen(),
            routes: [_productRoute('/wishlist')],
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/shopping',
            builder: (context, state) => const ShoppingListScreen(),
            routes: [_productRoute('/shopping')],
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
            routes: [
              GoRoute(
                path: 'stores', // полный адрес: /profile/stores
                builder: (context, state) => const StoresScreen(),
              ),
            ],
          ),
        ]),
      ],
    ),
  ],
);
