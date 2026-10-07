// screens/stores_screen.dart
// Магазины, цены которых отслеживает приложение.
import 'package:flutter/material.dart';
import '../data/mock_data.dart';
import '../widgets/store_card.dart';

class StoresScreen extends StatelessWidget {
  const StoresScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Магазины')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: mockStores.length,
        separatorBuilder: (context, index) => const SizedBox(height: 8),
        itemBuilder: (context, index) => StoreCard(store: mockStores[index]),
      ),
    );
  }
}
