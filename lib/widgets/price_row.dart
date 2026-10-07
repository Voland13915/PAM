// widgets/price_row.dart
// Строка «название — цена»: цены по магазинам (детали) и товары в группе
// магазина (список покупок).
import 'package:flutter/material.dart';
import '../utils/formatters.dart';

class PriceRow extends StatelessWidget {
  final String label;
  final double price;
  final double? oldPrice;
  final bool isBest;
  final bool inStock;
  final String? subtitle; // если null — статус наличия

  const PriceRow({
    super.key,
    required this.label,
    required this.price,
    this.oldPrice,
    this.isBest = false,
    this.inStock = true,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final status = !inStock
        ? 'Нет в наличии'
        : isBest
            ? 'Лучшая цена'
            : 'В наличии';

    final priceColor = !inStock
        ? scheme.onSurfaceVariant
        : isBest
            ? scheme.primary
            : scheme.onSurface;

    return ListTile(
      leading: Icon(
        isBest ? Icons.verified : Icons.storefront_outlined,
        color: isBest ? scheme.primary : scheme.onSurfaceVariant,
      ),
      title: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(
        subtitle ?? status,
        style: text.bodySmall?.copyWith(
          color: inStock ? scheme.onSurfaceVariant : scheme.error,
        ),
      ),
      trailing: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(
            formatPrice(price),
            style: text.titleMedium?.copyWith(
              fontWeight: isBest ? FontWeight.w700 : FontWeight.w500,
              color: priceColor,
            ),
          ),
          if (oldPrice != null)
            Text(
              formatPrice(oldPrice!),
              style: text.bodySmall?.copyWith(
                color: scheme.onSurfaceVariant,
                decoration: TextDecoration.lineThrough,
              ),
            ),
        ],
      ),
    );
  }
}
