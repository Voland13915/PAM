import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/wishlist_item.dart';
import '../models/catalog_model.dart';
import '../models/wishlist_model.dart';
import '../utils/formatters.dart';
import '../widgets/error_view.dart';
import '../widgets/product_card.dart';

class WishlistScreen extends StatelessWidget {
  const WishlistScreen({super.key});

  Future<bool> _confirmRemove(
      BuildContext context, WishlistItem item, String productName) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Перестать следить?'),
        content: Text(productName),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Удалить'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return false;

    final error = await context.read<WishlistModel>().remove(item.id);
    if (!context.mounted) return error == null; // экран мог исчезнуть
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(error ?? 'Слежение отключено: $productName')),
    );
    return error == null;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final wishlist = context.watch<WishlistModel>();
    final catalog = context.watch<CatalogModel>();

    final Widget body;
    if (wishlist.isLoading || catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (wishlist.error != null || catalog.error != null) {
      body = ErrorView(
        message: (wishlist.error ?? catalog.error)!,
        onRetry: () {
          // read в callback-е; перезагружаем только то, что упало
          if (wishlist.error != null) context.read<WishlistModel>().load();
          if (catalog.error != null) context.read<CatalogModel>().load();
        },
      );
    } else if (wishlist.items.isEmpty) {
      body = const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Пока ни за чем не следите. Откройте товар и нажмите «Следить».',
            textAlign: TextAlign.center,
          ),
        ),
      );
    } else {
      final items = wishlist.items;
      body = Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              'Уведомим, когда цена опустится до желаемой. '
              'Смахните карточку влево, чтобы перестать следить.',
              style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
            ),
          ),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              itemCount: items.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = items[index];
                final product = catalog.byId(item.productId);
                if (product == null) return const SizedBox.shrink();
                return Dismissible(
                  key: ValueKey(item.id), // идентичность из данных
                  direction: DismissDirection.endToStart,
                  confirmDismiss: (_) =>
                      _confirmRemove(context, item, product.name),
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
                  child: ProductCard(
                    product: product,
                    onTap: () => context.push('/wishlist/${product.id}'),
                    footer: _TargetPriceInfo(
                      targetPrice: item.targetPrice,
                      reached: product.bestOffer.price <= item.targetPrice,
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Избранное'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Обновить',
            onPressed: wishlist.isLoading
                ? null
                : () => context.read<WishlistModel>().load(),
          ),
        ],
      ),
      body: body,
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
        color:
            reached ? scheme.tertiaryContainer : scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            reached ? Icons.check_circle : Icons.notifications_active_outlined,
            size: 18,
            color:
                reached ? scheme.onTertiaryContainer : scheme.onSurfaceVariant,
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
