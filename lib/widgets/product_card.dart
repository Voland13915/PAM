import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data/product.dart';
import '../models/catalog_model.dart';
import '../utils/formatters.dart';
import 'color_picker.dart';
import 'product_image.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback? onTap;
  final Widget? footer;
  final int? storeId;

  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
    this.footer,
    this.storeId,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final best = product.bestOffer;
    final catalog = context.watch<CatalogModel>();
    final bestStoreName = catalog.storeName(best.storeId);
    final count = product.offers.length;
    final storeOffer = storeId == null
        ? null
        : product.offers.where((o) => o.storeId == storeId).firstOrNull;

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
                        if (product.colors.length > 1) ...[
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              for (final c in product.colors.take(6))
                                Padding(
                                  padding: const EdgeInsets.only(right: 4),
                                  child: ColorSwatchDot(hex: c.hex, size: 12),
                                ),
                              if (product.colors.length > 6)
                                Text(
                                  '+${product.colors.length - 6}',
                                  style: text.bodySmall,
                                ),
                            ],
                          ),
                        ],
                        const SizedBox(height: 8),
                        if (storeOffer != null)
                          _StorePrice(
                            offer: storeOffer,
                            best: best,
                            bestStoreName: bestStoreName,
                            stores: product.offers.where((o) => o.inStock).length,
                          )
                        else if (product.isAvailable)
                          Wrap(
                            spacing: 8,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              Text(
                                'от ${formatPrice(best.price)}',
                                style: text.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w700,
                                  color: scheme.primary,
                                ),
                              ),
                              Text(
                                'в $bestStoreName',
                                style: text.bodySmall,
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
                        if (storeOffer == null)
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

class _StorePrice extends StatelessWidget {
  final Offer offer;
  final Offer best;
  final String bestStoreName;
  final int stores;

  const _StorePrice({
    required this.offer,
    required this.best,
    required this.bestStoreName,
    required this.stores,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final elsewhere = best.storeId != offer.storeId && best.inStock;
    final String note;
    final Color noteColor;
    if (!offer.inStock && elsewhere) {
      note = 'Есть в $bestStoreName: ${formatPrice(best.price)}';
      noteColor = scheme.onSurfaceVariant;
    } else if (elsewhere && best.price < offer.price) {
      note = 'Дешевле в $bestStoreName: ${formatPrice(best.price)}';
      noteColor = scheme.error;
    } else if (offer.inStock && stores > 1) {
      note = 'Лучшая цена среди $stores ${storesWord(stores)}';
      noteColor = scheme.primary;
    } else if (offer.inStock) {
      note = 'Есть только в этом магазине';
      noteColor = scheme.onSurfaceVariant;
    } else {
      note = 'Последняя цена ${formatPrice(offer.price)}';
      noteColor = scheme.onSurfaceVariant;
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          offer.inStock ? formatPrice(offer.price) : 'Нет в наличии',
          style: text.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
            color: offer.inStock ? scheme.primary : scheme.error,
          ),
        ),
        Text(note, style: text.bodySmall?.copyWith(color: noteColor)),
      ],
    );
  }
}
