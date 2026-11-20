import 'package:flutter/material.dart';

import '../data/product.dart';

Color swatchColor(String hex) {
  final value = int.tryParse(hex.replaceFirst('#', ''), radix: 16);
  return value == null ? Colors.grey : Color(0xFF000000 | value);
}

class ColorSwatchDot extends StatelessWidget {
  final String hex;
  final double size;

  const ColorSwatchDot({super.key, required this.hex, this.size = 18});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: swatchColor(hex),
        shape: BoxShape.circle,
        border: Border.all(color: Theme.of(context).colorScheme.outline),
      ),
    );
  }
}

class ProductColorPicker extends StatelessWidget {
  final List<ProductColor> colors;
  final String? selected;
  final ValueChanged<String?> onSelected;

  const ProductColorPicker({
    super.key,
    required this.colors,
    required this.selected,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    ProductColor? current;
    for (final c in colors) {
      if (c.code == selected) current = c;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          current == null ? 'Цвет: любой' : 'Цвет: ${current.name}',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ChoiceChip(
              label: const Text('Любой'),
              selected: selected == null,
              onSelected: (_) => onSelected(null),
            ),
            for (final color in colors)
              ChoiceChip(
                avatar: ColorSwatchDot(hex: color.hex),
                label: Text(
                  color.name,
                  style: color.isAvailable
                      ? null
                      : TextStyle(
                          color: scheme.onSurfaceVariant,
                          decoration: TextDecoration.lineThrough,
                        ),
                ),
                tooltip: color.isAvailable ? null : 'Нет в наличии',
                selected: selected == color.code,
                onSelected: (_) => onSelected(color.code),
              ),
          ],
        ),
      ],
    );
  }
}
