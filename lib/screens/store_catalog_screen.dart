import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data/product_repository.dart';
import '../data/store_repository.dart';
import '../models/catalog_model.dart';
import 'catalog_screen.dart';

class StoreCatalogScreen extends StatelessWidget {
  final int storeId;

  const StoreCatalogScreen({super.key, required this.storeId});

  @override
  Widget build(BuildContext context) {
    final name = context.select<CatalogModel, String?>(
            (catalog) => catalog.storeById(storeId)?.name) ??
        'Магазин';
    return ChangeNotifierProvider(
      create: (context) => CatalogModel(
        context.read<ProductRepository>(),
        context.read<StoreRepository>(),
        storeId: storeId,
      )..load(),
      child: CatalogScreen(
        title: name,
        basePath: '/profile/stores/$storeId',
      ),
    );
  }
}
