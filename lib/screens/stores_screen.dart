import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/catalog_model.dart';
import '../widgets/error_view.dart';
import '../widgets/store_card.dart';
import '../widgets/sync_card.dart';

class StoresScreen extends StatelessWidget {
  const StoresScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final catalog = context.watch<CatalogModel>();
    final stores = catalog.stores;

    final Widget body;
    if (catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (catalog.error != null) {
      body = ErrorView(
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(),
      );
    } else {
      body = ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: stores.length + 1,
        separatorBuilder: (context, index) => const SizedBox(height: 8),
        itemBuilder: (context, index) => index == 0
            ? const SyncCard()
            : StoreCard(
                key: ValueKey(stores[index - 1].id),
                store: stores[index - 1],
                onTap: () =>
                    context.push('/profile/stores/${stores[index - 1].id}'),
              ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Магазины')),
      body: body,
    );
  }
}
