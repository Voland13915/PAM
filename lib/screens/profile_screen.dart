import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/auth_api.dart';
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
    if (ok != true || !context.mounted) return;
    await context.read<AuthApi>().logout();
    if (!context.mounted) return;
    context.read<ShoppingListModel>().clear();
    context.read<SessionModel>().signOut();
    context.go('/login');
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

    final loading = catalog.isLoading || wishlist.isLoading;
    final loadError = catalog.error ?? wishlist.error;

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
                value: wishlist.isLoading
                    ? '…'
                    : wishlist.error != null
                        ? '—'
                        : '${wishlist.items.length}',
                label: 'в избранном',
              ),
              const SizedBox(width: 8),
              _StatTile(value: '${shopping.count}', label: 'в списке'),
              const SizedBox(width: 8),
              _StatTile(
                value: catalog.isLoading
                    ? '…'
                    : catalog.error != null
                        ? '—'
                        : formatPrice(savings),
                label: 'экономия',
              ),
            ],
          ),
          if (!loading && loadError != null) ...[
            const SizedBox(height: 12),
            _LoadErrorCard(
              message: loadError,
              onRetry: () {
                if (catalog.error != null) context.read<CatalogModel>().load();
                if (wishlist.error != null) {
                  context.read<WishlistModel>().load();
                }
              },
            ),
          ],

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
                      : catalog.error != null
                          ? 'не удалось загрузить'
                          : '${catalog.stores.length} магазинов'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/profile/stores'),
                ),
              ],
            ),
          ),

          const SectionTitle('О приложении'),
          const Card(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  InfoRow(label: 'Версия', value: '0.5.0 (L5)'),
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

class _LoadErrorCard extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _LoadErrorCard({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Card(
      color: scheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
        child: Row(
          children: [
            Icon(Icons.cloud_off, color: scheme.onErrorContainer),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: scheme.onErrorContainer),
              ),
            ),
            TextButton(
              onPressed: onRetry,
              child: const Text('Повторить'),
            ),
          ],
        ),
      ),
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
