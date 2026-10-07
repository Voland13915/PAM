// screens/shopping_list_screen.dart
// Список покупок: выбранные товары, итог и где что выгоднее купить.
// Упрощённая версия: каждый товар — в магазине с минимальной ценой.
// Оптимальное распределение с учётом маршрута (графы) — часть диплома.
import 'package:flutter/material.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';
import '../widgets/info_row.dart';
import '../widgets/price_row.dart';
import '../widgets/product_card.dart';

class ShoppingListScreen extends StatelessWidget {
  const ShoppingListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final items = mockShoppingListIds.map(productById).toList();
    final bestTotal =
        items.fold<double>(0, (sum, p) => sum + p.bestOffer.price);
    final maxTotal = items.fold<double>(0, (sum, p) => sum + p.maxPrice);

    // Группировка: магазин -> товары, которые в нём дешевле всего.
    final byStore = <int, List<Product>>{};
    for (final p in items) {
      byStore.putIfAbsent(p.bestOffer.storeId, () => []).add(p);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Список покупок')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Итог
          Card(
            color: scheme.primaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Товаров в списке: ${items.length}',
                    style: text.bodyMedium
                        ?.copyWith(color: scheme.onPrimaryContainer),
                  ),
                  const SizedBox(height: 8),
                  InfoRow(
                    label: 'По лучшим ценам',
                    value: formatPrice(bestTotal),
                    emphasize: true,
                  ),
                  InfoRow(
                    label: 'По самым высоким ценам',
                    value: formatPrice(maxTotal),
                  ),
                  InfoRow(
                    label: 'Экономия',
                    value: formatPrice(maxTotal - bestTotal),
                  ),
                ],
              ),
            ),
          ),

          const SectionTitle('Где покупать'),
          for (final entry in byStore.entries)
            Card(
              child: Column(
                children: [
                  ListTile(
                    leading: CircleAvatar(
                      backgroundColor: scheme.secondaryContainer,
                      foregroundColor: scheme.onSecondaryContainer,
                      child: Text(storeById(entry.key).name[0]),
                    ),
                    title: Text(storeById(entry.key).name,
                        style: text.titleMedium),
                    subtitle: Text('Товаров: ${entry.value.length}'),
                    trailing: Text(
                      formatPrice(entry.value
                          .fold<double>(0, (s, p) => s + p.bestOffer.price)),
                      style: text.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  const Divider(height: 1),
                  for (final p in entry.value)
                    PriceRow(
                      label: p.name,
                      price: p.bestOffer.price,
                      oldPrice: p.bestOffer.oldPrice,
                      isBest: true,
                      subtitle: p.category,
                    ),
                ],
              ),
            ),

          const SectionTitle('Товары'),
          for (final p in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: ProductCard(product: p),
            ),
        ],
      ),
    );
  }
}
