import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../utils/formatters.dart';
import 'price_alerts.dart';

class Notifications {
  Notifications._();

  static final _plugin = FlutterLocalNotificationsPlugin();
  static Future<void>? _ready;

  static const _channel = AndroidNotificationDetails(
    'price_alerts',
    'Снижение цен',
    channelDescription: 'Цена отслеживаемого товара опустилась до вашей',
    importance: Importance.high,
    priority: Priority.high,
  );

  static Future<void> init({void Function(int productId)? onOpen}) =>
      _ready ??= _initialize(onOpen);

  static Future<void> _initialize(void Function(int productId)? onOpen) async {
    await _plugin.initialize(
      const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      ),
      onDidReceiveNotificationResponse: (response) {
        final id = int.tryParse(response.payload ?? '');
        if (id != null) onOpen?.call(id);
      },
    );
  }

  static Future<int?> launchedFromProduct() async {
    final details = await _plugin.getNotificationAppLaunchDetails();
    if (details == null || !details.didNotificationLaunchApp) return null;
    return int.tryParse(details.notificationResponse?.payload ?? '');
  }

  static Future<bool> requestPermission() async {
    final android = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    return await android?.requestNotificationsPermission() ?? true;
  }

  static Future<void> showAlert(PriceAlert alert, String storeName) async {
    await init();
    await _plugin.show(
      alert.item.id,
      'Цена снизилась: ${alert.product.name}',
      '${formatPrice(alert.offer.price)} в $storeName — '
          'ваша цена ${formatPrice(alert.item.targetPrice)}',
      const NotificationDetails(android: _channel),
      payload: '${alert.product.id}',
    );
  }
}
