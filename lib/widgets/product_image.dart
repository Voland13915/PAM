// widgets/product_image.dart
// Заглушка изображения: иконка категории на фоне из темы.
import 'package:flutter/material.dart';

class ProductImage extends StatelessWidget {
  final String category;
  final double size;

  const ProductImage({super.key, required this.category, this.size = 64});

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
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(size * 0.2),
      ),
      child: Icon(iconFor(category), size: size * 0.5, color: scheme.primary),
    );
  }
}
