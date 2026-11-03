import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/mock_network.dart';
import '../data/product.dart';
import '../models/catalog_model.dart';
import '../models/session_model.dart';
import '../models/shopping_list_model.dart';
import '../models/wishlist_model.dart';
import '../utils/formatters.dart';
import '../widgets/info_row.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  Future<void> _logout(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Выйти из аккаунта?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Нет'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Да, выйти'),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      context.read<SessionModel>().signOut();
      context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final session = context.watch<SessionModel>();
    final wishlist = context.watch<WishlistModel>();
    final shopping = context.watch<ShoppingListModel>();
    final catalog = context.watch<CatalogModel>();

    final name = session.displayName;
    final initials = name.isEmpty ? '?' : name[0].toUpperCase();

    final savings = shopping.productIds
        .map(catalog.byId)
        .whereType<Product>()
        .fold<double>(0, (sum, p) => sum + p.priceSpread);

    return Scaffold(
      appBar: AppBar(title: const Text('Профиль')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Center(
            child: CircleAvatar(
              radius: 40,
              backgroundColor: scheme.primaryContainer,
              foregroundColor: scheme.onPrimaryContainer,
              child: Text(initials, style: text.headlineSmall),
            ),
          ),
          const SizedBox(height: 12),
          Text(name, textAlign: TextAlign.center, style: text.titleLarge),
          if (session.email != null)
            Text(
              session.email!,
              textAlign: TextAlign.center,
              style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
            ),
          const SizedBox(height: 16),
          Row(
            children: [
              _StatTile(
                value: wishlist.isLoading ? '…' : '${wishlist.items.length}',
                label: 'в избранном',
              ),
              const SizedBox(width: 8),
              _StatTile(value: '${shopping.count}', label: 'в списке'),
              const SizedBox(width: 8),
              _StatTile(value: formatPrice(savings), label: 'экономия'),
            ],
          ),

          const SectionTitle('Настройки'),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  secondary: const Icon(Icons.notifications_active_outlined),
                  title: const Text('Уведомления о снижении цены'),
                  value: true,
                  onChanged: (_) {},
                ),
                ListTile(
                  leading: const Icon(Icons.storefront_outlined),
                  title: const Text('Отслеживаемые магазины'),
                  subtitle: Text(catalog.isLoading
                      ? 'загружается…'
                      : '${catalog.stores.length} магазинов'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/profile/stores'),
                ),
              ],
            ),
          ),

          const SectionTitle('Демонстрация (L4)'),
          const Card(child: _NetworkFailureSwitch()),

          const SectionTitle('О приложении'),
          const Card(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  InfoRow(label: 'Версия', value: '0.4.0 (L4)'),
                  InfoRow(label: 'Валюта', value: 'MDL'),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () => _logout(context),
            icon: const Icon(Icons.logout),
            label: const Text('Выйти из аккаунта'),
          ),
        ],
      ),
    );
  }
}

class _NetworkFailureSwitch extends StatefulWidget {
  const _NetworkFailureSwitch();

  @override
  State<_NetworkFailureSwitch> createState() => _NetworkFailureSwitchState();
}

class _NetworkFailureSwitchState extends State<_NetworkFailureSwitch> {
  late bool _enabled;

  @override
  void initState() {
    super.initState();
    _enabled = context.read<MockNetwork>().simulateError;
  }

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      secondary: const Icon(Icons.cloud_off_outlined),
      title: const Text('Симулировать сбой сети'),
      subtitle: const Text('Любой запрос к хранилищу вернёт ошибку'),
      value: _enabled,
      onChanged: (value) {
        setState(() => _enabled = value);
        context.read<MockNetwork>().simulateError = value;
      },
    );
  }
}

class _StatTile extends StatelessWidget {
  final String value;
  final String label;

  const _StatTile({required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            FittedBox(
              child: Text(value,
                  style: text.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
            ),
            Text(label,
                style:
                    text.bodySmall?.copyWith(color: scheme.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}
