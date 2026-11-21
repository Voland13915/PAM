import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

import '../data/token_store.dart';
import '../models/app_settings.dart';
import '../models/wishlist_model.dart';
import '../router.dart';
import '../services/background.dart';
import '../services/notifications.dart';
import '../services/price_check.dart';

class PriceAlertsHost extends StatefulWidget {
  final String apiBase;
  final TokenStore tokens;
  final Widget child;

  const PriceAlertsHost({
    super.key,
    required this.apiBase,
    required this.tokens,
    required this.child,
  });

  @override
  State<PriceAlertsHost> createState() => _PriceAlertsHostState();
}

class _PriceAlertsHostState extends State<PriceAlertsHost> {
  late final AppLifecycleListener _lifecycle;
  WishlistModel? _wishlist;
  AppSettings? _settings;
  bool _started = false;
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    _lifecycle = AppLifecycleListener(onResume: _check);
    Notifications.init(onOpen: _openProduct).then((_) async {
      final productId = await Notifications.launchedFromProduct();
      if (productId != null) {
        WidgetsBinding.instance
            .addPostFrameCallback((_) => _openProduct(productId));
      }
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final wishlist = context.read<WishlistModel>();
    if (!identical(wishlist, _wishlist)) {
      _wishlist?.removeListener(_onWishlistChanged);
      _wishlist = wishlist..addListener(_onWishlistChanged);
    }
    final settings = context.read<AppSettings?>();
    if (!identical(settings, _settings)) {
      _settings?.removeListener(_onSettingsChanged);
      _settings = settings?..addListener(_onSettingsChanged);
    }
  }

  bool get _enabled => _settings?.notifications ?? true;

  void _onSettingsChanged() {
    if (_enabled) {
      _onWishlistChanged();
    } else if (_started) {
      _started = false;
      cancelBackgroundChecks().catchError(
          (Object error) => debugPrint('Фоновая проверка не остановлена: $error'));
    }
  }

  @override
  void dispose() {
    _wishlist?.removeListener(_onWishlistChanged);
    _settings?.removeListener(_onSettingsChanged);
    _lifecycle.dispose();
    super.dispose();
  }

  void _openProduct(int productId) => router.push('/wishlist/$productId');

  void _onWishlistChanged() {
    if (!_enabled) return;
    final watching = _wishlist?.items.any((i) => i.notify) ?? false;
    if (!watching) return;
    _start();
    _check();
  }

  Future<void> _start() async {
    if (_started) return;
    _started = true;
    try {
      final allowed = await Notifications.requestPermission();
      debugPrint('Уведомления разрешены: $allowed');
      await scheduleBackgroundChecks();
    } catch (error) {
      debugPrint('Фоновая проверка не запущена: $error');
      _started = false;
    }
  }

  Future<void> _check() async {
    if (_checking || !_enabled) return;
    _checking = true;
    try {
      final sent = await runPriceCheck(widget.apiBase, tokens: widget.tokens);
      debugPrint('Проверка цен: уведомлений $sent');
    } catch (error) {
      debugPrint('Проверка цен не удалась: $error');
    } finally {
      _checking = false;
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
