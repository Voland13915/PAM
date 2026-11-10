import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/catalog_model.dart';
import '../models/shopping_list_model.dart';
import '../models/wishlist_model.dart';
import '../utils/formatters.dart';
import '../widgets/info_row.dart';
import '../widgets/missing_product_view.dart';
import '../widgets/price_history_chart.dart';
import '../widgets/price_row.dart';
import '../widgets/product_image.dart';

class ProductDetailsScreen extends StatelessWidget {
  final int productId;
  final String basePath;

  const ProductDetailsScreen({
    super.key,
    required this.productId,
    required this.basePath,
  });

  void _snack(BuildContext context, String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final catalog = context.watch<CatalogModel>();
    final inList = context.watch<ShoppingListModel>().contains(productId);
    final tracked =
        context.watch<WishlistModel>().byProduct(productId) != null;

    final product = catalog.byId(productId);
    if (product == null) {
      return const MissingProductView();
    }

    final best = product.bestOffer;
    final offers = [...product.offers]
      ..sort((a, b) => a.price.compareTo(b.price));

    return Scaffold(
      appBar: AppBar(
        title: Text(product.brand),
        actions: [
          IconButton(
            icon: Icon(tracked ? Icons.favorite : Icons.favorite_border),
            tooltip: tracked ? 'Изменить слежение' : 'Следить за ценой',
            onPressed: () => context.push('$basePath/$productId/track'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Center(
            child: ProductImage(category: product.category, size: 160),
          ),
          const SizedBox(height: 16),
          Text(product.name, style: text.headlineSmall),
          const SizedBox(height: 4),
          Text(
            product.category,
            style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),

          Card(
            color: scheme.primaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.local_offer,
                      color: scheme.onPrimaryContainer, size: 32),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Дешевле всего в ${catalog.storeName(best.storeId)}',
                          style: text.bodyMedium
                              ?.copyWith(color: scheme.onPrimaryContainer),
                        ),
                        Text(
                          formatPrice(best.price),
                          style: text.headlineSmall?.copyWith(
                            fontWeight: FontWeight.w700,
                            color: scheme.onPrimaryContainer,
                          ),
                        ),
                        if (product.priceSpread > 0)
                          Text(
                            'Разница между магазинами: '
                            '${formatPrice(product.priceSpread)}',
                            style: text.bodySmall
                                ?.copyWith(color: scheme.onPrimaryContainer),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SectionTitle('Цены в магазинах'),
          Card(
            child: Column(
              children: [
                for (final offer in offers)
                  PriceRow(
                    label: catalog.storeName(offer.storeId),
                    price: offer.price,
                    oldPrice: offer.oldPrice,
                    isBest: offer == best,
                    inStock: offer.inStock,
                  ),
              ],
            ),
          ),

          const SectionTitle('Минимальная цена за 6 месяцев'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: PriceHistoryChart(prices: product.priceHistory),
            ),
          ),

          const SectionTitle('Характеристики'),
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  for (final spec in product.specs.entries)
                    InfoRow(label: spec.key, value: spec.value),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () =>
                      context.push('$basePath/$productId/track'),
                  icon: Icon(tracked
                      ? Icons.notifications_active
                      : Icons.notifications_outlined),
                  label: Text(tracked ? 'Изменить' : 'Следить'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: inList
                    ? FilledButton.tonalIcon(
                        // read в callback-е: действие, а не подписка
                        onPressed: () {
                          context.read<ShoppingListModel>().remove(productId);
                          _snack(context, 'Убрано из списка покупок');
                        },
                        icon: const Icon(Icons.remove_shopping_cart),
                        label: const Text('Убрать'),
                      )
                    : FilledButton.icon(
                        onPressed: () {
                          context.read<ShoppingListModel>().add(productId);
                          _snack(context, 'Добавлено в список покупок');
                        },
                        icon: const Icon(Icons.add_shopping_cart),
                        label: const Text('В список'),
                      ),
              ),
            ],
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}
