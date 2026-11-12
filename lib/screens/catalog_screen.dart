import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/catalog_model.dart';
import '../widgets/error_view.dart';
import '../widgets/product_card.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  late final TextEditingController _searchCtrl;

  @override
  void initState() {
    super.initState();
    _searchCtrl =
        TextEditingController(text: context.read<CatalogModel>().search);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _search(String query) =>
      context.read<CatalogModel>().load(search: query.trim());

  void _clearSearch() {
    _searchCtrl.clear();
    _search('');
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final catalog = context.watch<CatalogModel>();

    final Widget body;
    if (catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (catalog.error != null) {
      body = ErrorView(
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(),
      );
    } else {
      body = _CatalogContent(catalog: catalog);
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Каталог'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Обновить',
            onPressed: catalog.isLoading
                ? null
                : () => context.read<CatalogModel>().load(),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: TextField(
              controller: _searchCtrl,
              textInputAction: TextInputAction.search,
              onSubmitted: _search,
              decoration: InputDecoration(
                hintText: 'Поиск по названию, бренду или категории',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: catalog.search.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close),
                        tooltip: 'Сбросить поиск',
                        onPressed: _clearSearch,
                      ),
                filled: true,
                fillColor: scheme.surfaceContainerHighest,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(28),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          Expanded(child: body),
        ],
      ),
    );
  }
}

class _CatalogContent extends StatelessWidget {
  final CatalogModel catalog;

  const _CatalogContent({required this.catalog});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final products = catalog.products;
    final categories = catalog.categories;

    if (products.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            catalog.search.isEmpty
                ? 'Каталог пуст'
                : 'По запросу «${catalog.search}» ничего не найдено',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return Column(
      children: [
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
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              catalog.search.isEmpty
                  ? 'Показано товаров: ${products.length}'
                  : 'Найдено по «${catalog.search}»: ${products.length}'
                      '${catalog.hasMore ? '+' : ''}',
              style: text.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
            itemCount: products.length + (catalog.hasMore ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == products.length) return _ListTail(catalog: catalog);
              final product = products[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: ProductCard(
                  key: ValueKey(product.id),
                  product: product,
                  onTap: () => context.push('/catalog/${product.id}'),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _ListTail extends StatelessWidget {
  final CatalogModel catalog;

  const _ListTail({required this.catalog});

  @override
  Widget build(BuildContext context) {
    if (catalog.loadMoreError != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          children: [
            Text(catalog.loadMoreError!, textAlign: TextAlign.center),
            TextButton(
              onPressed: catalog.retryLoadMore,
              child: const Text('Повторить'),
            ),
          ],
        ),
      );
    }
    catalog.loadMore();
    return const Padding(
      padding: EdgeInsets.all(16),
      child: Center(
        child: SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
    );
  }
}
