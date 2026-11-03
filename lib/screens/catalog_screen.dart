// screens/catalog_screen.dart
// Каталог: три состояния — грузится / данные / ошибка с retry (C8).
// Данные приходят из CatalogModel, а не из mock-а: экран не знает источника.
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/product.dart';
import '../models/catalog_model.dart';
import '../widgets/error_view.dart';
import '../widgets/product_card.dart';

class CatalogScreen extends StatelessWidget {
  const CatalogScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final catalog = context.watch<CatalogModel>(); // watch в build (C7)

    final Widget body;
    if (catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator()); // 1) грузится
    } else if (catalog.error != null) {
      body = ErrorView(
        // 2) упало
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(), // read: действие
      );
    } else {
      body = _CatalogContent(
        // 3) данные
        products: catalog.products,
        categories: catalog.categories,
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Каталог'),
        actions: [
          IconButton(
            // Повторная загрузка: с включённой аварией показывает ошибку
            icon: const Icon(Icons.refresh),
            tooltip: 'Обновить',
            onPressed: catalog.isLoading
                ? null
                : () => context.read<CatalogModel>().load(), // read: действие
          ),
        ],
      ),
      body: body,
    );
  }
}

/// Поиск, фильтры и список — тот же layout, что на L2–L3.
/// Фильтры пока визуальные.
class _CatalogContent extends StatelessWidget {
  final List<Product> products;
  final List<String> categories;

  const _CatalogContent({required this.products, required this.categories});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          child: TextField(
            decoration: InputDecoration(
              hintText: 'Поиск по названию или бренду',
              prefixIcon: const Icon(Icons.search),
              filled: true,
              fillColor: scheme.surfaceContainerHighest,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(28),
                borderSide: BorderSide.none,
              ),
            ),
          ),
        ),
        // Фильтр по категории: категории выводит модель из загруженных товаров
        SizedBox(
          height: 48,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: categories.length + 1,
            separatorBuilder: (context, index) => const SizedBox(width: 8),
            itemBuilder: (context, index) => FilterChip(
              label: Text(index == 0 ? 'Все' : categories[index - 1]),
              selected: index == 0,
              onSelected: (_) {},
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                ActionChip(
                  avatar: const Icon(Icons.storefront_outlined, size: 18),
                  label: const Text('Все магазины'),
                  onPressed: () {},
                ),
                ActionChip(
                  avatar: const Icon(Icons.sort, size: 18),
                  label: const Text('Сначала дешёвые'),
                  onPressed: () {},
                ),
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Найдено товаров: ${products.length}',
              style: text.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
            ),
          ),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
            itemCount: products.length,
            separatorBuilder: (context, index) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final product = products[index];
              return ProductCard(
                key: ValueKey(product.id), // идентичность из данных (C7)
                product: product,
                onTap: () => context.push('/catalog/${product.id}'),
              );
            },
          ),
        ),
      ],
    );
  }
}
