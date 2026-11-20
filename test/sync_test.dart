import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/data/result.dart';
import 'package:tech_price/data/sync_status.dart';
import 'package:tech_price/models/catalog_model.dart';
import 'package:tech_price/utils/formatters.dart';

import 'fakes.dart';

void main() {
  test('SyncStatus читает ответ сервера', () {
    final status = SyncStatus.fromJson({
      'enabled': true,
      'running': false,
      'nextAt': '2026-11-20T04:00:00+02:00',
      'lastSync': '2026-11-19T02:10:00Z',
      'exitCode': 1,
    });
    expect(status.enabled, isTrue);
    expect(status.nextAt, DateTime.parse('2026-11-20T02:00:00Z').toLocal());
    expect(status.lastSync, isNotNull);
    expect(status.failed, isTrue);
    expect(SyncStatus.fromJson(const {}).failed, isFalse);
  });

  test('formatNextRun говорит «сегодня» и «завтра»', () {
    final now = DateTime(2026, 11, 19, 13, 0);
    expect(formatNextRun(DateTime(2026, 11, 19, 23, 5), now: now),
        'сегодня в 23:05');
    expect(formatNextRun(DateTime(2026, 11, 20, 4, 0), now: now),
        'завтра в 04:00');
    expect(formatNextRun(DateTime(2026, 11, 22, 4, 0), now: now),
        startsWith('22'));
  });

  test('Обновление цен запускается один раз', () async {
    final stores = FakeStoreRepository();
    final catalog = CatalogModel(FakeProductRepository([]), stores);

    expect(await catalog.startSync(), isA<Ok<SyncStatus>>());
    expect(await catalog.startSync(), isA<Err<SyncStatus>>());
    expect(stores.syncStarts, 1);
    final status = await catalog.syncStatus();
    expect(status, isA<Ok<SyncStatus>>());
  });
}
