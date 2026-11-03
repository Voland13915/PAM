// widgets/app_shell.dart — обёртка с постоянными вкладками.
// StatelessWidget: текущий индекс вкладки знает router.
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/shopping_list_model.dart';

class AppShell extends StatelessWidget {
  final StatefulNavigationShell navigationShell;

  const AppShell({super.key, required this.navigationShell});

  /// Иконка «Покупки» с badge: один живой угол — Consumer (C7).
  /// Перестраивается только badge, а не вся панель.
  Widget _cartIcon(IconData icon) => Consumer<ShoppingListModel>(
        builder: (context, list, child) => Badge(
          isLabelVisible: list.count > 0,
          label: Text('${list.count}'),
          child: child!,
        ),
        child: Icon(icon),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell, // содержимое текущей вкладки
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: navigationShell.goBranch, // переключает вкладку
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.grid_view_outlined),
            selectedIcon: Icon(Icons.grid_view),
            label: 'Каталог',
          ),
          const NavigationDestination(
            icon: Icon(Icons.favorite_border),
            selectedIcon: Icon(Icons.favorite),
            label: 'Избранное',
          ),
          NavigationDestination(
            icon: _cartIcon(Icons.shopping_cart_outlined),
            selectedIcon: _cartIcon(Icons.shopping_cart),
            label: 'Покупки',
          ),
          const NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Профиль',
          ),
        ],
      ),
    );
  }
}
