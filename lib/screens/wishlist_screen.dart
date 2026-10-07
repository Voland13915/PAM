// screens/wishlist_screen.dart
// Избранное: товары, за ценой которых пользователь следит,
// с желаемой ценой и отметкой, если она достигнута.
import 'package:flutter/material.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';
import '../widgets/product_card.dart';

class WishlistScreen extends StatelessWidget {
  const WishlistScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Избранное')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              'Уведомим, когда цена опустится до желаемой.',
              style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
            ),
          ),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              itemCount: mockWishlist.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = mockWishlist[index];
                final product = productById(item.productId);
                return ProductCard(
                  product: product,
                  footer: _TargetPriceInfo(
                    targetPrice: item.targetPrice,
                    reached: product.bestOffer.price <= item.targetPrice,
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _TargetPriceInfo extends StatelessWidget {
  final double targetPrice;
  final bool reached;

  const _TargetPriceInfo({required this.targetPrice, required this.reached});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: reached ? scheme.tertiaryContainer : scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            reached ? Icons.check_circle : Icons.notifications_active_outlined,
            size: 18,
            color: reached ? scheme.onTertiaryContainer : scheme.onSurfaceVariant,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              reached
                  ? 'Желаемая цена достигнута: до ${formatPrice(targetPrice)}'
                  : 'Желаемая цена: до ${formatPrice(targetPrice)}',
              style: text.bodySmall?.copyWith(
                color: reached
                    ? scheme.onTertiaryContainer
                    : scheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
