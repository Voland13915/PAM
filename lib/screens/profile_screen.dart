import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';
import '../widgets/info_row.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  // Блокирующее решение → AlertDialog с результатом (C6).
  Future<void> _logout(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Выйти из аккаунта?'),
        actions: [
          TextButton(
            // dialogCtx, а не context: под вложенными навигаторами вкладок
            // pop по context-у экрана закрыл бы не диалог
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
    // ok == true, а не ok!: диалог, закрытый мимо, возвращает null
    if (ok == true && context.mounted) {
      context.go('/login'); // go: раздел с вкладками уходит из стека
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    final initials = mockUser.name.split(' ').map((w) => w[0]).join();

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
          Text(mockUser.name,
              textAlign: TextAlign.center, style: text.titleLarge),
          Text(
            mockUser.email,
            textAlign: TextAlign.center,
            style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _StatTile(value: '${mockWishlist.length}', label: 'в избранном'),
              const SizedBox(width: 8),
              _StatTile(
                  value: '${mockShoppingListIds.length}', label: 'в списке'),
              const SizedBox(width: 8),
              _StatTile(
                  value: formatPrice(mockUser.savedTotal),
                  label: 'сэкономлено'),
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
                SwitchListTile(
                  secondary: const Icon(Icons.dark_mode_outlined),
                  title: const Text('Тёмная тема'),
                  value: false,
                  onChanged: (_) {},
                ),
                ListTile(
                  leading: const Icon(Icons.location_city_outlined),
                  title: const Text('Город'),
                  trailing: Text(mockUser.city),
                ),
                ListTile(
                  leading: const Icon(Icons.storefront_outlined),
                  title: const Text('Отслеживаемые магазины'),
                  subtitle: Text('${mockStores.length} магазинов'),
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
                  InfoRow(label: 'Версия', value: '0.3.0 (L3)'),
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
