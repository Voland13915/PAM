import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data/product.dart';
import '../models/catalog_model.dart';
import '../utils/formatters.dart';
import 'product_image.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback? onTap;
  final Widget? footer;

  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
    this.footer,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final best = product.bestOffer;
    final bestStoreName =
        context.watch<CatalogModel>().storeName(best.storeId);
    final count = product.offers.length;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ProductImage(
                    category: product.category,
                    imageUrl: product.imageUrl,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          product.name,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: text.titleSmall,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          product.category,
                          style: text.bodySmall
                              ?.copyWith(color: scheme.onSurfaceVariant),
                        ),
                        const SizedBox(height: 8),
                        if (product.isAvailable)
                          Row(
                            children: [
                              Text(
                                'от ${formatPrice(best.price)}',
                                style: text.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w700,
                                  color: scheme.primary,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Flexible(
                                child: Text(
                                  'в $bestStoreName',
                                  overflow: TextOverflow.ellipsis,
                                  style: text.bodySmall,
                                ),
                              ),
                            ],
                          )
                        else
                          Text(
                            'Нет в наличии',
                            style: text.titleSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: scheme.error,
                            ),
                          ),
                        Text(
                          product.isAvailable
                              ? 'Цены в $count ${storesWord(count)}'
                              : 'Последняя цена ${formatPrice(best.price)}',
                          style: text.bodySmall
                              ?.copyWith(color: scheme.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (footer != null) ...[
                const SizedBox(height: 10),
                footer!,
              ],
            ],
          ),
        ),
      ),
    );
  }
}
