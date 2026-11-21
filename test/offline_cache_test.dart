import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tech_price/data/api_client.dart';
import 'package:tech_price/data/offline_status.dart';
import 'package:tech_price/data/response_cache.dart';
import 'package:tech_price/data/result.dart';
import 'package:tech_price/data/token_store.dart';

void main() {
  late Directory dir;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('techprice_cache');
  });

  tearDown(() async {
    if (await dir.exists()) await dir.delete(recursive: true);
  });

  ResponseCache cacheAt(DateTime now) => ResponseCache(
        directory: () async => Directory('${dir.path}/api'),
        clock: () => now,
      );

  test('Сохранённый ответ читается, пока не устарел', () async {
    final now = DateTime(2026, 11, 20, 12);
    await cacheAt(now).write('/products?page=1', '{"a":1}');

    final fresh = await cacheAt(now.add(const Duration(days: 6)))
        .read('/products?page=1');
    expect(fresh?.body, '{"a":1}');
    expect(fresh?.savedAt, now);

    expect(
        await cacheAt(now.add(const Duration(days: 8))).read('/products?page=1'),
        isNull);
    expect(await cacheAt(now).read('/products?page=2'), isNull);
  });

  test('Очистка удаляет все сохранённые ответы', () async {
    final now = DateTime(2026, 11, 20, 12);
    final cache = cacheAt(now);
    await cache.write('/wishlist', '{"items":[]}');
    await cache.clear();
    expect(await cache.read('/wishlist'), isNull);
  });

  test('Имена файлов разные для разных запросов', () {
    expect(ResponseCache.fileName('/products?page=1'),
        isNot(ResponseCache.fileName('/products?page=2')));
    expect(ResponseCache.fileName('/x'), ResponseCache.fileName('/x'));
  });

  group('ApiClient', () {
    late ResponseCache cache;
    late OfflineStatus offline;
    late ApiClient api;

    setUp(() {
      cache = ResponseCache(directory: () async => Directory('${dir.path}/api'));
      offline = OfflineStatus();
      api = ApiClient('http://server', TokenStore(), cache: cache, offline: offline);
    });

    Future<Result<int>> getNumber() => api.send(
          'GET',
          '/number',
          auth: false,
          parse: (json) => (json as Map<String, dynamic>)['n'] as int,
        );

    Future<Result<int>> withServer(http.Response response) =>
        http.runWithClient(getNumber, () => MockClient((_) async => response));

    Future<Result<int>> withoutNetwork() => http.runWithClient(
          getNumber,
          () => MockClient((_) async => throw http.ClientException('нет сети')),
        );

    test('Без сети GET отдаёт сохранённый ответ', () async {
      final online = await withServer(http.Response('{"n":5}', 200));
      expect(online, isA<Ok<int>>());
      expect((online as Ok<int>).savedAt, isNull);
      expect(offline.isOffline, isFalse);

      final cached = await withoutNetwork();
      expect(cached, isA<Ok<int>>());
      expect((cached as Ok<int>).value, 5);
      expect(cached.savedAt, isNotNull);
      expect(offline.isOffline, isTrue);

      await withServer(http.Response('{"n":6}', 200));
      expect(offline.isOffline, isFalse);
    });

    test('Сервер с ошибкой 5xx тоже заменяется сохранённым ответом', () async {
      await withServer(http.Response('{"n":7}', 200));
      final cached = await withServer(http.Response('{"error":{}}', 503));
      expect((cached as Ok<int>).value, 7);
    });

    test('Без сохранённого ответа остаётся ошибка', () async {
      expect(await withoutNetwork(), isA<Err<int>>());
      expect(offline.isOffline, isFalse);
    });

    test('Изменения без сети не подменяются кешем', () async {
      final result = await http.runWithClient(
        () => api.send<void>('POST', '/number',
            auth: false, okStatus: 201, body: const {}, parse: (_) {}),
        () => MockClient((_) async => throw http.ClientException('нет сети')),
      );
      expect(result, isA<Err<void>>());
    });
  });
}
