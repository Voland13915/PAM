import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/auth_api.dart';
import '../data/image_cache.dart';
import '../data/offline_status.dart';
import '../data/product.dart';
import '../data/response_cache.dart';
import '../data/result.dart';
import '../models/app_settings.dart';
import '../models/catalog_model.dart';
import '../models/savings_report.dart';
import '../models/session_model.dart';
import '../models/shopping_list_model.dart';
import '../models/wishlist_model.dart';
import '../utils/formatters.dart';
import '../utils/validators.dart';
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
    await context.read<ResponseCache>().clear();
    if (!context.mounted) return;
    context.read<OfflineStatus>().online();
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
    final settings = context.watch<AppSettings>();

    final name = session.displayName;
    final initials = name.isEmpty ? '?' : name[0].toUpperCase();

    final savings = SavingsReport.of(shopping.productIds
            .map(catalog.byId)
            .whereType<Product>())
        .saving(settings.savingsBaseline);
    final watched = wishlist.items.where((i) => i.notify).length;

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
                onTap: () => context.go('/wishlist'),
              ),
              const SizedBox(width: 8),
              _StatTile(
                value: '${shopping.count}',
                label: 'в списке',
                onTap: () => context.go('/shopping'),
              ),
              const SizedBox(width: 8),
              _StatTile(
                value: catalog.isLoading
                    ? '…'
                    : catalog.error != null
                        ? '—'
                        : formatPrice(savings),
                label: 'экономия',
                onTap: () => context.push('/profile/savings'),
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

          const SectionTitle('Аккаунт'),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.badge_outlined),
                  title: const Text('Имя'),
                  subtitle: Text(name),
                  trailing: const Icon(Icons.edit_outlined),
                  onTap: () => showDialog<void>(
                    context: context,
                    builder: (_) => _NameDialog(initial: name),
                  ),
                ),
                ListTile(
                  leading: const Icon(Icons.password),
                  title: const Text('Сменить пароль'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => showDialog<void>(
                    context: context,
                    builder: (_) => const _PasswordDialog(),
                  ),
                ),
              ],
            ),
          ),

          const SectionTitle('Уведомления'),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  secondary: const Icon(Icons.notifications_active_outlined),
                  title: const Text('Уведомления о снижении цены'),
                  subtitle: Text(settings.notifications
                      ? 'Проверка при открытии приложения и раз в час в фоне'
                      : 'Выключены для всех товаров'),
                  value: settings.notifications,
                  onChanged: (value) =>
                      context.read<AppSettings>().setNotifications(value),
                ),
                ListTile(
                  leading: const Icon(Icons.favorite_outline),
                  title: const Text('Отслеживаемые товары'),
                  subtitle: Text(wishlist.isLoading
                      ? 'загружается…'
                      : 'С уведомлением: $watched из ${wishlist.items.length}'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.go('/wishlist'),
                ),
              ],
            ),
          ),

          const SectionTitle('Магазины и экономия'),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.storefront_outlined),
                  title: const Text('Отслеживаемые магазины'),
                  subtitle: Text(catalog.isLoading
                      ? 'загружается…'
                      : catalog.error != null
                          ? 'не удалось загрузить'
                          : '${catalog.stores.length} магазинов · каталог каждого'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/profile/stores'),
                ),
                ListTile(
                  leading: const Icon(Icons.savings_outlined),
                  title: const Text('Подробно об экономии'),
                  subtitle: const Text('Где, как и на чём вы экономите'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/profile/savings'),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Считать экономию от цены', style: text.bodyLarge),
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        child: SegmentedButton<SavingsBaseline>(
                          segments: const [
                            ButtonSegment(
                              value: SavingsBaseline.highest,
                              label: Text('Самой высокой'),
                            ),
                            ButtonSegment(
                              value: SavingsBaseline.average,
                              label: Text('Средней'),
                            ),
                          ],
                          selected: {settings.savingsBaseline},
                          onSelectionChanged: (value) => context
                              .read<AppSettings>()
                              .setSavingsBaseline(value.first),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SectionTitle('Оформление'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Тема', style: text.bodyLarge),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: SegmentedButton<ThemeMode>(
                      segments: const [
                        ButtonSegment(
                          value: ThemeMode.system,
                          icon: Icon(Icons.brightness_auto_outlined),
                          label: Text('Авто'),
                        ),
                        ButtonSegment(
                          value: ThemeMode.light,
                          icon: Icon(Icons.light_mode_outlined),
                          label: Text('Светлая'),
                        ),
                        ButtonSegment(
                          value: ThemeMode.dark,
                          icon: Icon(Icons.dark_mode_outlined),
                          label: Text('Тёмная'),
                        ),
                      ],
                      selected: {settings.themeMode},
                      onSelectionChanged: (value) =>
                          context.read<AppSettings>().setThemeMode(value.first),
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SectionTitle('Данные'),
          const Card(child: _CacheTile()),

          const SectionTitle('О приложении'),
          const Card(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  InfoRow(label: 'Версия', value: '0.6.0'),
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
  final VoidCallback onTap;

  const _StatTile({
    required this.value,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Expanded(
      child: Material(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
            child: Column(
              children: [
                FittedBox(
                  child: Text(value,
                      style: text.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700)),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Flexible(
                      child: Text(label,
                          overflow: TextOverflow.ellipsis,
                          style: text.bodySmall
                              ?.copyWith(color: scheme.onSurfaceVariant)),
                    ),
                    Icon(Icons.chevron_right,
                        size: 14, color: scheme.onSurfaceVariant),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NameDialog extends StatefulWidget {
  final String initial;

  const _NameDialog({required this.initial});

  @override
  State<_NameDialog> createState() => _NameDialogState();
}

class _NameDialogState extends State<_NameDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _ctrl =
      TextEditingController(text: widget.initial);
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    final name = _ctrl.text.trim();
    setState(() {
      _busy = true;
      _error = null;
    });
    final result = await context.read<AuthApi>().updateName(name);
    if (!mounted) return;
    switch (result) {
      case Ok(:final value):
        context.read<SessionModel>().rename(value.name);
        final messenger = ScaffoldMessenger.of(context);
        Navigator.pop(context);
        messenger.showSnackBar(const SnackBar(content: Text('Имя сохранено')));
      case Err(:final msg):
        setState(() {
          _busy = false;
          _error = msg;
        });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Имя'),
      content: Form(
        key: _formKey,
        child: TextFormField(
          controller: _ctrl,
          autofocus: true,
          maxLength: 60,
          textCapitalization: TextCapitalization.words,
          textInputAction: TextInputAction.done,
          onFieldSubmitted: (_) => _save(),
          decoration: InputDecoration(
            labelText: 'Как к вам обращаться',
            border: const OutlineInputBorder(),
            errorText: _error,
          ),
          validator: validateName,
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.pop(context),
          child: const Text('Отмена'),
        ),
        FilledButton(
          onPressed: _busy ? null : _save,
          child: const Text('Сохранить'),
        ),
      ],
    );
  }
}

class _PasswordDialog extends StatefulWidget {
  const _PasswordDialog();

  @override
  State<_PasswordDialog> createState() => _PasswordDialogState();
}

class _PasswordDialogState extends State<_PasswordDialog> {
  final _formKey = GlobalKey<FormState>();
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _repeat = TextEditingController();
  bool _busy = false;
  bool _visible = false;
  String? _error;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _repeat.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final result =
        await context.read<AuthApi>().changePassword(_current.text, _next.text);
    if (!mounted) return;
    switch (result) {
      case Ok():
        final messenger = ScaffoldMessenger.of(context);
        Navigator.pop(context);
        messenger.showSnackBar(const SnackBar(content: Text('Пароль изменён')));
      case Err(:final msg):
        setState(() {
          _busy = false;
          _error = msg;
        });
    }
  }

  InputDecoration _decoration(String label, {String? error}) => InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        errorText: error,
      );

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Смена пароля'),
      content: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _current,
                obscureText: !_visible,
                autofocus: true,
                decoration: _decoration('Текущий пароль', error: _error),
                validator: (value) => value == null || value.isEmpty
                    ? 'Введите текущий пароль'
                    : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _next,
                obscureText: !_visible,
                decoration: _decoration('Новый пароль'),
                validator: (value) {
                  final error = validatePassword(value);
                  if (error != null) return error;
                  if (value == _current.text) return 'Совпадает с текущим';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _repeat,
                obscureText: !_visible,
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _save(),
                decoration: _decoration('Повторите новый пароль'),
                validator: (value) =>
                    value != _next.text ? 'Пароли не совпадают' : null,
              ),
              CheckboxListTile(
                value: _visible,
                onChanged: (value) => setState(() => _visible = value ?? false),
                title: const Text('Показать пароли'),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.pop(context),
          child: const Text('Отмена'),
        ),
        FilledButton(
          onPressed: _busy ? null : _save,
          child: const Text('Сменить'),
        ),
      ],
    );
  }
}

class _CacheTile extends StatefulWidget {
  const _CacheTile();

  @override
  State<_CacheTile> createState() => _CacheTileState();
}

class _CacheTileState extends State<_CacheTile> {
  late Future<int> _size;

  @override
  void initState() {
    super.initState();
    _size = context.read<ResponseCache>().size();
  }

  Future<void> _clear() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Очистить кэш?'),
        content: const Text(
            'Удалятся сохранённые каталоги и фото товаров. Без связи с '
            'сервером приложение не сможет показать их, пока не загрузит заново.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Очистить'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    final cache = context.read<ResponseCache>();
    await cache.clear();
    await productImages.emptyCache();
    if (!mounted) return;
    setState(() => _size = cache.size());
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Кэш очищен')));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<int>(
      future: _size,
      builder: (context, snapshot) => ListTile(
        leading: const Icon(Icons.cleaning_services_outlined),
        title: const Text('Очистить кэш'),
        subtitle: Text(snapshot.hasData
            ? 'Офлайн-данные: ${formatBytes(snapshot.data!)} + фото товаров'
            : 'Считаем размер…'),
        onTap: _clear,
      ),
    );
  }
}
