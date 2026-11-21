import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/product.dart';
import '../models/app_settings.dart';
import '../models/catalog_model.dart';
import '../models/savings_report.dart';
import '../models/shopping_list_model.dart';
import '../utils/formatters.dart';
import '../widgets/error_view.dart';
import '../widgets/flexible_tile.dart';
import '../widgets/info_row.dart';

class SavingsScreen extends StatelessWidget {
  const SavingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final catalog = context.watch<CatalogModel>();
    final list = context.watch<ShoppingListModel>();

    final Widget body;
    if (catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (catalog.error != null) {
      body = ErrorView(
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(),
      );
    } else {
      final report = SavingsReport.of(
          list.productIds.map(catalog.byId).whereType<Product>());
      body = report.isEmpty
          ? const _Empty()
          : _Report(report: report, pending: list.count - report.items.length - report.unavailable.length);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Экономия')),
      body: body,
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.savings_outlined, size: 56, color: scheme.onSurfaceVariant),
            const SizedBox(height: 12),
            const Text(
              'Экономия считается по списку покупок. Добавьте товары '
              'кнопкой «В список» — и здесь появится, где и на чём '
              'получается сэкономить.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => context.go('/catalog'),
              icon: const Icon(Icons.storefront_outlined),
              label: const Text('Открыть каталог'),
            ),
          ],
        ),
      ),
    );
  }
}

class _Report extends StatelessWidget {
  final SavingsReport report;
  final int pending;

  const _Report({required this.report, required this.pending});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final settings = context.watch<AppSettings>();
    final catalog = context.watch<CatalogModel>();
    final baseline = settings.savingsBaseline;
    final total = report.saving(baseline);
    final stores = report.byStore(baseline);
    final categories = report.byCategory(baseline);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        SegmentedButton<SavingsBaseline>(
          segments: const [
            ButtonSegment(
              value: SavingsBaseline.highest,
              label: Text('От самой высокой'),
            ),
            ButtonSegment(
              value: SavingsBaseline.average,
              label: Text('От средней'),
            ),
          ],
          selected: {baseline},
          onSelectionChanged: (value) =>
              context.read<AppSettings>().setSavingsBaseline(value.first),
        ),
        const SizedBox(height: 12),
        Card(
          color: scheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Вы экономите',
                  style: text.bodyMedium
                      ?.copyWith(color: scheme.onPrimaryContainer),
                ),
                Text(
                  formatPrice(total),
                  style: text.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: scheme.onPrimaryContainer,
                  ),
                ),
                Text(
                  '${formatPercent(report.percent(baseline))} от суммы '
                  '${baseline == SavingsBaseline.highest ? 'по самым высоким' : 'по средним'} '
                  'ценам · ${report.items.length} ${itemsWord(report.items.length)}',
                  style: text.bodySmall
                      ?.copyWith(color: scheme.onPrimaryContainer),
                ),
                const Divider(height: 24),
                InfoRow(
                  label: 'По лучшим ценам',
                  value: formatPrice(report.bestTotal),
                  emphasize: true,
                ),
                InfoRow(
                  label: 'По средним ценам',
                  value: formatPrice(report.averageTotal),
                ),
                InfoRow(
                  label: 'По самым высоким',
                  value: formatPrice(report.highestTotal),
                ),
                if (report.discounts > 0)
                  InfoRow(
                    label: 'Из них скидки магазинов',
                    value: formatPrice(report.discounts),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        _HowItWorks(baseline: baseline),
        const SectionTitle('Где покупать'),
        for (final store in stores)
          Card(
            child: FlexibleTile(
              onTap: () => context.push('/profile/stores/${store.storeId}'),
              leading: CircleAvatar(
                backgroundColor: scheme.secondaryContainer,
                foregroundColor: scheme.onSecondaryContainer,
                child: Text(catalog.storeName(store.storeId)[0]),
              ),
              title: Text(catalog.storeName(store.storeId)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${store.items.length} ${itemsWord(store.items.length)} '
                      'на ${formatPrice(store.total)}'),
                  const SizedBox(height: 6),
                  LinearProgressIndicator(
                    value: total <= 0 ? 0 : store.saving(baseline) / total,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ],
              ),
              trailing: _Saving(store.saving(baseline)),
            ),
          ),
        const SectionTitle('На чём экономим'),
        Card(
          child: Column(
            children: [
              for (final entry in report.ranked(baseline).indexed) ...[
                if (entry.$1 > 0) const Divider(height: 1),
                _ItemTile(item: entry.$2, baseline: baseline),
              ],
            ],
          ),
        ),
        if (categories.length > 1) ...[
          const SectionTitle('По категориям'),
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  for (final c in categories)
                    InfoRow(
                      label: '${c.category} (${c.count})',
                      value: formatPrice(c.saving),
                    ),
                ],
              ),
            ),
          ),
        ],
        if (report.unavailable.isNotEmpty || pending > 0) ...[
          const SectionTitle('Не учтено'),
          Card(
            child: Column(
              children: [
                for (final p in report.unavailable)
                  ListTile(
                    leading: Icon(Icons.remove_shopping_cart_outlined,
                        color: scheme.error),
                    title: Text(p.name,
                        maxLines: 2, overflow: TextOverflow.ellipsis),
                    subtitle: const Text('Сейчас нет в наличии ни в одном магазине'),
                    onTap: () => context.push('/profile/savings/${p.id}'),
                  ),
                if (pending > 0)
                  ListTile(
                    leading: const Icon(Icons.hourglass_empty),
                    title: Text('Загружается: $pending'),
                  ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _HowItWorks extends StatelessWidget {
  final SavingsBaseline baseline;

  const _HowItWorks({required this.baseline});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    final rule = baseline == SavingsBaseline.highest
        ? 'разница между самой высокой ценой среди магазинов, где товар '
            'есть в наличии, и самой низкой. Это максимум, который можно '
            'переплатить, если покупать не глядя.'
        : 'разница между средней ценой по магазинам, где товар есть в '
            'наличии, и самой низкой. Это то, что вы обычно выигрываете '
            'по сравнению со «случайным» магазином.';
    return Card(
      child: ExpansionTile(
        leading: const Icon(Icons.info_outline),
        title: const Text('Как считается экономия'),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Для каждого товара из списка покупок — $rule',
              style: text.bodyMedium),
          const SizedBox(height: 8),
          Text(
            'Товары, которые продаются только в одном магазине, сравнить не '
            'с чем — их экономия 0. Товары не в наличии не учитываются. '
            '«Скидки магазинов» — насколько лучшая цена ниже старой цены, '
            'которую указал сам магазин.',
            style: text.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}

class _ItemTile extends StatelessWidget {
  final ItemSaving item;
  final SavingsBaseline baseline;

  const _ItemTile({required this.item, required this.baseline});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final catalog = context.watch<CatalogModel>();
    final bestStore = catalog.storeName(item.best.storeId);

    final String details;
    if (!item.comparable) {
      details = 'Только в $bestStore за ${formatPrice(item.best.price)} — '
          'сравнить не с чем';
    } else if (baseline == SavingsBaseline.highest) {
      details = 'Купить в $bestStore за ${formatPrice(item.best.price)}\n'
          'Дороже всего в ${catalog.storeName(item.highest.storeId)}: '
          '${formatPrice(item.highest.price)}';
    } else {
      details = 'Купить в $bestStore за ${formatPrice(item.best.price)}\n'
          'Средняя цена в ${item.stores} ${storesWord(item.stores)}: '
          '${formatPrice(item.average)}';
    }

    return FlexibleTile(
      onTap: () => context.push('/profile/savings/${item.product.id}'),
      title: Text(item.product.name,
          maxLines: 2, overflow: TextOverflow.ellipsis),
      subtitle: Text(details),
      trailing: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          _Saving(item.saving(baseline)),
          if (item.comparable)
            Text(
              formatPercent(item.percent(baseline)),
              style: text.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
            ),
        ],
      ),
    );
  }
}

class _Saving extends StatelessWidget {
  final double value;

  const _Saving(this.value);

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    return Text(
      value > 0 ? '−${formatPrice(value)}' : formatPrice(0),
      style: text.titleSmall?.copyWith(
        fontWeight: FontWeight.w700,
        color: value > 0 ? scheme.primary : scheme.onSurfaceVariant,
      ),
    );
  }
}
