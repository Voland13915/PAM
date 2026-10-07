// screens/profile_screen.dart
// Профиль: данные пользователя, статистика, настройки (переключатели
// пока не меняют состояние — это L4).
import 'package:flutter/material.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';
import '../widgets/info_row.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

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
                  trailing: Text('${mockStores.length}'),
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
                  InfoRow(label: 'Версия', value: '0.2.0 (L2)'),
                  InfoRow(label: 'Валюта', value: 'MDL'),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () {},
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
