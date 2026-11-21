import 'package:flutter/material.dart';
import '../data/store.dart';
import '../utils/formatters.dart';
import 'flexible_tile.dart';

class StoreCard extends StatelessWidget {
  final Store store;
  final VoidCallback? onTap;

  const StoreCard({super.key, required this.store, this.onTap});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: FlexibleTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: scheme.primaryContainer,
          foregroundColor: scheme.onPrimaryContainer,
          child: Text(store.name[0]),
        ),
        title: Text(store.name, style: text.titleMedium),
        subtitle: Text(
            '${store.website}\nОбновлено: ${formatSyncTime(store.lastSync)}'),
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
