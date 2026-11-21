import 'package:flutter/widgets.dart';
import 'package:workmanager/workmanager.dart';

import '../models/app_settings.dart';
import 'price_check.dart';

const priceCheckTask = 'price-check';
const _apiBase = String.fromEnvironment(
  'API_BASE',
  defaultValue: 'http://10.0.2.2:8080',
);

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    WidgetsFlutterBinding.ensureInitialized();
    try {
      if (!await AppSettings.notificationsAllowed()) return true;
      await runPriceCheck(_apiBase);
    } catch (_) {
      return false;
    }
    return true;
  });
}

Future<void> scheduleBackgroundChecks() async {
  await Workmanager().initialize(callbackDispatcher);
  await Workmanager().registerPeriodicTask(
    priceCheckTask,
    priceCheckTask,
    frequency: const Duration(hours: 1),
  );
}

Future<void> cancelBackgroundChecks() async {
  await Workmanager().initialize(callbackDispatcher);
  await Workmanager().cancelByUniqueName(priceCheckTask);
}
