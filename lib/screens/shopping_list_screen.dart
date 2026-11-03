import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/product.dart';
import '../models/catalog_model.dart';
import '../models/shopping_list_model.dart';
import '../utils/formatters.dart';
import '../widgets/error_view.dart';
import '../widgets/info_row.dart';
import '../widgets/price_row.dart';
import '../widgets/product_card.dart';

class ShoppingListScreen extends StatelessWidget {
  const ShoppingListScreen({super.key});

  Future<void> _confirmClear(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Очистить список покупок?'),
        content: const Text('Все товары будут удалены из списка.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Очистить'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    context.read<ShoppingListModel>().clear(); // read: действие
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Список покупок очищен')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final list = context.watch<ShoppingListModel>();
    final catalog = context.watch<CatalogModel>();

    final Widget body;
    if (catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (catalog.error != null) {
      body = ErrorView(
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(),
      );
    } else {
      final items = [
        for (final id in list.productIds) catalog.byId(id),
      ].whereType<Product>().toList();
      body = items.isEmpty ? const _EmptyList() : _ListContent(items: items);
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Список покупок'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined),
            tooltip: 'Очистить список',
            onPressed: list.count == 0 ? null : () => _confirmClear(context),
          ),
        ],
      ),
      body: body,
    );
  }
}

class _EmptyList extends StatelessWidget {
  const _EmptyList();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.shopping_cart_outlined,
                size: 56, color: scheme.onSurfaceVariant),
            const SizedBox(height: 12),
            const Text(
              'Список пуст. Добавьте товары кнопкой «В список» '
              'на экране товара.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ListContent extends StatelessWidget {
  final List<Product> items;

  const _ListContent({required this.items});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final catalog = context.watch<CatalogModel>();

    final bestTotal =
        items.fold<double>(0, (sum, p) => sum + p.bestOffer.price);
    final maxTotal = items.fold<double>(0, (sum, p) => sum + p.maxPrice);

    final byStore = <int, List<Product>>{};
    for (final p in items) {
      byStore.putIfAbsent(p.bestOffer.storeId, () => []).add(p);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
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
                    child: Text(catalog.storeName(entry.key)[0]),
                  ),
                  title: Text(catalog.storeName(entry.key),
                      style: text.titleMedium),
                  subtitle: Text('Товаров: ${entry.value.length}'),
                  trailing: Text(
                    formatPrice(entry.value
                        .fold<double>(0, (s, p) => s + p.bestOffer.price)),
                    style:
                        text.titleMedium?.copyWith(fontWeight: FontWeight.w700),
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

        const SectionTitle('Товары (смахните, чтобы убрать)'),
        for (final p in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Dismissible(
              // Идентичность из данных, а не UniqueKey (C7)
              key: ValueKey(p.id),
              direction: DismissDirection.endToStart,
              background: Container(
                alignment: Alignment.centerRight,
                padding: const EdgeInsets.symmetric(horizontal: 24),
                decoration: BoxDecoration(
                  color: scheme.errorContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.delete_outline,
                    color: scheme.onErrorContainer),
              ),
              onDismissed: (_) {
                context.read<ShoppingListModel>().remove(p.id);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Убрано из списка: ${p.name}')),
                );
              },
              child: ProductCard(
                product: p,
                onTap: () => context.push('/shopping/${p.id}'),
              ),
            ),
          ),
      ],
    );
  }
}
