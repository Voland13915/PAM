// widgets/store_card.dart
// Карточка магазина: экран «Магазины» (повторяется в списке).
import 'package:flutter/material.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';

class StoreCard extends StatelessWidget {
  final Store store;
  final VoidCallback? onTap;

  const StoreCard({super.key, required this.store, this.onTap});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Card(
      child: ListTile(
        onTap: onTap,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: CircleAvatar(
          backgroundColor: scheme.primaryContainer,
          foregroundColor: scheme.onPrimaryContainer,
          child: Text(store.name[0]),
        ),
        title: Text(store.name, style: text.titleMedium),
        subtitle: Text('${store.website}\nОбновлено ${store.lastSync}'),
        isThreeLine: true,
        trailing: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              formatNumber(store.productsTracked.toDouble()),
              style: text.titleMedium?.copyWith(color: scheme.primary),
            ),
            Text('товаров', style: text.bodySmall),
          ],
        ),
      ),
    );
  }
}
