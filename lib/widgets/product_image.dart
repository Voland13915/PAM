import 'package:flutter/material.dart';

class ProductImage extends StatelessWidget {
  final String category;
  final String imageUrl;
  final double size;

  const ProductImage({
    super.key,
    required this.category,
    this.imageUrl = '',
    this.size = 64,
  });

  static IconData iconFor(String category) => switch (category) {
        'Смартфоны' => Icons.smartphone,
        'Ноутбуки' => Icons.laptop,
        'Телевизоры' => Icons.tv,
        'Наушники' => Icons.headphones,
        'Стиральные машины' => Icons.local_laundry_service,
        'Холодильники' => Icons.kitchen,
        'Пылесосы' => Icons.cleaning_services,
        'Микроволновки' => Icons.microwave,
        _ => Icons.devices_other,
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final radius = BorderRadius.circular(size * 0.2);

    Widget placeholder() => Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: scheme.surfaceContainerHighest,
            borderRadius: radius,
          ),
          child: Icon(iconFor(category), size: size * 0.5, color: scheme.primary),
        );

    if (imageUrl.isEmpty) return placeholder();

    return ClipRRect(
      borderRadius: radius,
      child: Container(
        width: size,
        height: size,
        color: Colors.white,
        padding: EdgeInsets.all(size * 0.06),
        child: Image.network(
          imageUrl,
          fit: BoxFit.contain,
          cacheWidth: (size * MediaQuery.devicePixelRatioOf(context)).round(),
          loadingBuilder: (context, child, progress) =>
              progress == null ? child : placeholder(),
          errorBuilder: (context, error, stackTrace) => placeholder(),
        ),
      ),
    );
  }
}
