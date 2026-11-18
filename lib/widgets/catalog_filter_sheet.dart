import 'package:flutter/material.dart';

import '../data/catalog_facets.dart';
import '../data/catalog_filter.dart';
import '../data/store.dart';
import '../utils/formatters.dart';

class CatalogFilterSheet extends StatefulWidget {
  final CatalogFilter filter;
  final CatalogFacets facets;
  final List<Store> stores;

  const CatalogFilterSheet({
    super.key,
    required this.filter,
    required this.facets,
    required this.stores,
  });

  @override
  State<CatalogFilterSheet> createState() => _CatalogFilterSheetState();
}

class _CatalogFilterSheetState extends State<CatalogFilterSheet> {
  static const _brandsCollapsed = 12;

  late CatalogFilter _draft = widget.filter;
  bool _allBrands = false;

  double get _lowest => (widget.facets.minPrice ?? 0).floorToDouble();
  double get _highest => (widget.facets.maxPrice ?? 0).ceilToDouble();

  RangeValues get _range => RangeValues(
        (_draft.minPrice ?? _lowest).clamp(_lowest, _highest).toDouble(),
        (_draft.maxPrice ?? _highest).clamp(_lowest, _highest).toDouble(),
      );

  void _setRange(RangeValues values) {
    final min = (values.start / 100).floorToDouble() * 100;
    final max = (values.end / 100).ceilToDouble() * 100;
    setState(() {
      _draft = _draft.copyWith(
        minPrice: () => min <= _lowest ? null : min,
        maxPrice: () => max >= _highest ? null : max,
      );
    });
  }

  void _toggleBrand(String brand, bool selected) {
    final brands = {..._draft.brands};
    selected ? brands.add(brand) : brands.remove(brand);
    setState(() => _draft = _draft.copyWith(brands: brands));
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final facets = widget.facets;

    final selectedMissing = _draft.brands
        .where((b) => !facets.brands.any((f) => f.name == b))
        .map((b) => FacetValue(b, 0));
    final allBrands = [...facets.brands, ...selectedMissing];
    final brands = _allBrands || allBrands.length <= _brandsCollapsed
        ? allBrands
        : allBrands.take(_brandsCollapsed).toList();
    final canSlide = _highest > _lowest;

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(
            child: ListView(
              shrinkWrap: true,
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
              children: [
                Text('Фильтры', style: text.titleLarge),
                const SizedBox(height: 16),
                Text('Магазин', style: text.titleSmall),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    ChoiceChip(
                      label: const Text('Любой'),
                      selected: _draft.storeId == null,
                      onSelected: (_) => setState(
                          () => _draft = _draft.copyWith(storeId: () => null)),
                    ),
                    for (final store in widget.stores)
                      ChoiceChip(
                        label: Text(
                            '${store.name} · ${facets.storeCount(store.id)}'),
                        selected: _draft.storeId == store.id,
                        onSelected: (_) => setState(() =>
                            _draft = _draft.copyWith(storeId: () => store.id)),
                      ),
                  ],
                ),
                if (canSlide) ...[
                  const SizedBox(height: 20),
                  Text('Цена', style: text.titleSmall),
                  RangeSlider(
                    values: _range,
                    min: _lowest,
                    max: _highest,
                    labels: RangeLabels(
                      formatPrice(_range.start),
                      formatPrice(_range.end),
                    ),
                    onChanged: _setRange,
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(formatPrice(_range.start)),
                      Text(formatPrice(_range.end)),
                    ],
                  ),
                ],
                if (allBrands.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Text('Бренд', style: text.titleSmall),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final brand in brands)
                        FilterChip(
                          label: Text(brand.count > 0
                              ? '${brand.name} · ${brand.count}'
                              : brand.name),
                          selected: _draft.brands.contains(brand.name),
                          onSelected: (selected) =>
                              _toggleBrand(brand.name, selected),
                        ),
                    ],
                  ),
                  if (allBrands.length > _brandsCollapsed)
                    Align(
                      alignment: Alignment.centerLeft,
                      child: TextButton(
                        onPressed: () =>
                            setState(() => _allBrands = !_allBrands),
                        child: Text(_allBrands
                            ? 'Свернуть'
                            : 'Все бренды (${allBrands.length})'),
                      ),
                    ),
                ],
                const SizedBox(height: 12),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Только со скидкой'),
                  value: _draft.onlyDiscount,
                  onChanged: (value) => setState(
                      () => _draft = _draft.copyWith(onlyDiscount: value)),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Показывать товары не в наличии'),
                  subtitle: const Text('С последней известной ценой'),
                  value: _draft.includeUnavailable,
                  onChanged: (value) => setState(() =>
                      _draft = _draft.copyWith(includeUnavailable: value)),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Есть в нескольких магазинах'),
                  subtitle: const Text('Можно сравнить цены'),
                  value: _draft.onlyMultiStore,
                  onChanged: (value) => setState(
                      () => _draft = _draft.copyWith(onlyMultiStore: value)),
                ),
              ],
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () =>
                          setState(() => _draft = _draft.cleared()),
                      child: const Text('Сбросить'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: () => Navigator.pop(context, _draft),
                      child: const Text('Показать'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
