import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/catalog_filter.dart';
import '../models/catalog_model.dart';
import '../utils/formatters.dart';
import '../widgets/catalog_filter_sheet.dart';
import '../widgets/error_view.dart';
import '../widgets/product_card.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  late final TextEditingController _searchCtrl;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _searchCtrl =
        TextEditingController(text: context.read<CatalogModel>().search);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchCtrl.dispose();
    super.dispose();
  }

  void _search(String query) {
    _debounce?.cancel();
    final catalog = context.read<CatalogModel>();
    if (query.trim() != catalog.search) catalog.load(search: query.trim());
  }

  void _onSearchChanged(String query) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () => _search(query));
    setState(() {});
  }

  void _clearSearch() {
    FocusManager.instance.primaryFocus?.unfocus();
    _searchCtrl.clear();
    _search('');
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final catalog = context.watch<CatalogModel>();

    final Widget body;
    if (catalog.error != null && !catalog.isLoading) {
      body = ErrorView(
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(),
      );
    } else if (catalog.isLoading && catalog.products.isEmpty) {
      body = const Center(child: CircularProgressIndicator());
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
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: TextField(
              controller: _searchCtrl,
              textInputAction: TextInputAction.search,
              onChanged: _onSearchChanged,
              onSubmitted: _search,
              onTapOutside: (_) =>
                  FocusManager.instance.primaryFocus?.unfocus(),
              decoration: InputDecoration(
                hintText: 'Модель, бренд или артикул',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchCtrl.text.isEmpty
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
          _FilterBar(catalog: catalog),
          SizedBox(
            height: 2,
            child: catalog.isLoading && catalog.products.isNotEmpty
                ? const LinearProgressIndicator()
                : null,
          ),
          Expanded(child: body),
        ],
      ),
    );
  }
}

class _FilterBar extends StatelessWidget {
  final CatalogModel catalog;

  const _FilterBar({required this.catalog});

  Future<void> _openFilters(BuildContext context) async {
    final result = await showModalBottomSheet<CatalogFilter>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (_) => CatalogFilterSheet(
        filter: catalog.filter,
        facets: catalog.facets,
        stores: catalog.stores,
      ),
    );
    if (result != null && context.mounted) {
      context.read<CatalogModel>().applyFilter(result);
    }
  }

  Future<void> _openSort(BuildContext context) async {
    final current = catalog.filter.sort;
    final result = await showModalBottomSheet<CatalogSort>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final sort in CatalogSort.values)
              ListTile(
                title: Text(sort.label),
                trailing: sort == current ? const Icon(Icons.check) : null,
                onTap: () => Navigator.pop(context, sort),
              ),
          ],
        ),
      ),
    );
    if (result != null && result != current && context.mounted) {
      context
          .read<CatalogModel>()
          .applyFilter(catalog.filter.copyWith(sort: result));
    }
  }

  void _apply(BuildContext context, CatalogFilter filter) {
    final current = catalog.filter;
    if (filter.category == current.category &&
        filter.activeCount == current.activeCount &&
        filter.sort == current.sort &&
        filter.toQuery().toString() == current.toQuery().toString()) {
      return;
    }
    context.read<CatalogModel>().applyFilter(filter);
  }

  @override
  Widget build(BuildContext context) {
    final filter = catalog.filter;
    final facets = catalog.facets;

    final active = <Widget>[
      for (final brand in filter.brands)
        InputChip(
          label: Text(brand),
          onDeleted: () => _apply(
              context, filter.copyWith(brands: {...filter.brands}..remove(brand))),
        ),
      if (filter.storeId != null)
        InputChip(
          label: Text(catalog.storeName(filter.storeId!)),
          onDeleted: () => _apply(context, filter.copyWith(storeId: () => null)),
        ),
      if (filter.hasPriceRange)
        InputChip(
          label: Text(_priceLabel(filter)),
          onDeleted: () => _apply(context,
              filter.copyWith(minPrice: () => null, maxPrice: () => null)),
        ),
      if (filter.onlyDiscount)
        InputChip(
          label: const Text('Со скидкой'),
          onDeleted: () => _apply(context, filter.copyWith(onlyDiscount: false)),
        ),
      if (filter.onlyMultiStore)
        InputChip(
          label: const Text('В 2+ магазинах'),
          onDeleted: () =>
              _apply(context, filter.copyWith(onlyMultiStore: false)),
        ),
      if (filter.includeUnavailable)
        InputChip(
          label: const Text('Включая нет в наличии'),
          onDeleted: () =>
              _apply(context, filter.copyWith(includeUnavailable: false)),
        ),
    ];

    return Column(
      children: [
        SizedBox(
          height: 48,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            children: [
              ChoiceChip(
                label: Text('Все · ${facets.categoriesTotal}'),
                selected: filter.category.isEmpty,
                onSelected: (_) => _apply(context, filter.copyWith(category: '')),
              ),
              for (final category in facets.categories) ...[
                const SizedBox(width: 8),
                ChoiceChip(
                  label: Text('${category.name} · ${category.count}'),
                  selected: filter.category == category.name,
                  onSelected: (_) =>
                      _apply(context, filter.copyWith(category: category.name)),
                ),
              ],
            ],
          ),
        ),
        SizedBox(
          height: 48,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            children: [
              ActionChip(
                avatar: Badge(
                  isLabelVisible: filter.activeCount > 0,
                  label: Text('${filter.activeCount}'),
                  child: const Icon(Icons.tune, size: 18),
                ),
                label: const Text('Фильтры'),
                onPressed: () => _openFilters(context),
              ),
              const SizedBox(width: 8),
              ActionChip(
                avatar: const Icon(Icons.sort, size: 18),
                label: Text(filter.sort.label),
                onPressed: () => _openSort(context),
              ),
              for (final chip in active) ...[
                const SizedBox(width: 8),
                chip,
              ],
            ],
          ),
        ),
      ],
    );
  }
}

String _priceLabel(CatalogFilter filter) {
  final min = filter.minPrice;
  final max = filter.maxPrice;
  if (min != null && max != null) {
    return '${formatNumber(min)} – ${formatPrice(max)}';
  }
  if (min != null) return 'от ${formatPrice(min)}';
  return 'до ${formatPrice(max!)}';
}

class _CatalogContent extends StatelessWidget {
  final CatalogModel catalog;

  const _CatalogContent({required this.catalog});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final products = catalog.products;
    final filtered = catalog.search.isNotEmpty || catalog.filter.activeCount > 0;

    if (products.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                filtered ? 'Ничего не найдено' : 'Каталог пуст',
                textAlign: TextAlign.center,
                style: text.titleMedium,
              ),
              if (catalog.filter.activeCount > 0) ...[
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => context
                      .read<CatalogModel>()
                      .applyFilter(catalog.filter.cleared()),
                  child: const Text('Сбросить фильтры'),
                ),
              ],
            ],
          ),
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              catalog.facets.total > 0
                  ? 'Найдено товаров: ${catalog.facets.total}'
                  : 'Показано товаров: ${products.length}',
              style: text.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
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
                  onTap: () {
                    FocusManager.instance.primaryFocus?.unfocus();
                    context.push('/catalog/${product.id}');
                  },
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
