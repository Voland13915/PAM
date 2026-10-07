// screens/home_screen.dart
// ВРЕМЕННЫЕ строительные леса L2 (Задание 6): по кнопке на экран,
// простой Navigator.push. На L3 этот экран удаляется — навигацию берёт go_router.
import 'package:flutter/material.dart';
import 'catalog_screen.dart';
import 'login_screen.dart';
import 'product_details_screen.dart';
import 'profile_screen.dart';
import 'shopping_list_screen.dart';
import 'stores_screen.dart';
import 'wishlist_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final entries = [
      _MenuEntry('Вход', 'Экран аутентификации', Icons.login,
          (_) => const LoginScreen()),
      _MenuEntry('Каталог', 'Поиск, фильтры, список товаров',
          Icons.grid_view, (_) => const CatalogScreen()),
      _MenuEntry('Детали товара', 'Цены в магазинах, история цены',
          Icons.info_outline, (_) => const ProductDetailsScreen(productId: 1)),
      _MenuEntry('Избранное', 'Отслеживаемые товары', Icons.favorite_border,
          (_) => const WishlistScreen()),
      _MenuEntry('Список покупок', 'Итог и где что дешевле',
          Icons.shopping_cart_outlined, (_) => const ShoppingListScreen()),
      _MenuEntry('Магазины', 'Отслеживаемые магазины',
          Icons.storefront_outlined, (_) => const StoresScreen()),
      _MenuEntry('Профиль', 'Пользователь и настройки', Icons.person_outline,
          (_) => const ProfileScreen()),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('TechPrice: экраны L2')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: entries.length,
        separatorBuilder: (context, index) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final e = entries[index];
          return Card(
            child: ListTile(
              leading: Icon(e.icon),
              title: Text(e.title),
              subtitle: Text(e.subtitle),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: e.builder),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _MenuEntry {
  final String title;
  final String subtitle;
  final IconData icon;
  final WidgetBuilder builder;

  const _MenuEntry(this.title, this.subtitle, this.icon, this.builder);
}
