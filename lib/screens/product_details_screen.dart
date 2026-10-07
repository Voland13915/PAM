// screens/product_details_screen.dart
// Детали товара: лучшая цена, цены во всех магазинах, история цены,
// характеристики. Экран получает только id и сам ищет товар —
// на L3 этот id придёт из адреса /products/:id.
import 'package:flutter/material.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';
import '../widgets/info_row.dart';
import '../widgets/price_history_chart.dart';
import '../widgets/price_row.dart';
import '../widgets/product_image.dart';

class ProductDetailsScreen extends StatelessWidget {
  final int productId;

  const ProductDetailsScreen({super.key, required this.productId});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final product = productById(productId);
    final best = product.bestOffer;
    final offers = [...product.offers]
      ..sort((a, b) => a.price.compareTo(b.price));

    return Scaffold(
      appBar: AppBar(
        title: Text(product.brand),
        actions: [
          IconButton(
            icon: const Icon(Icons.favorite_border),
            tooltip: 'В избранное',
            onPressed: () {},
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

          // Лучшая цена
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
                          'Дешевле всего в ${storeById(best.storeId).name}',
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
                    label: storeById(offer.storeId).name,
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
                  onPressed: () {},
                  icon: const Icon(Icons.notifications_outlined),
                  label: const Text('Следить'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton.icon(
                  onPressed: () {},
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
