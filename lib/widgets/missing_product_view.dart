import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/catalog_model.dart';
import 'error_view.dart';

class MissingProductView extends StatelessWidget {
  final String title;

  const MissingProductView({super.key, this.title = 'Товар'});

  @override
  Widget build(BuildContext context) {
    final catalog = context.watch<CatalogModel>(); // watch в build

    final Widget body;
    if (catalog.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (catalog.error != null) {
      body = ErrorView(
        message: catalog.error!,
        onRetry: () => context.read<CatalogModel>().load(), // read: действие
      );
    } else {
      body = const Center(child: Text('Товар не существует'));
    }

    return Scaffold(appBar: AppBar(title: Text(title)), body: body);
  }
}
