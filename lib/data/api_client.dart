import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'api_message.dart';
import 'offline_status.dart';
import 'response_cache.dart';
import 'result.dart';
import 'token_store.dart';

class ApiClient {
  ApiClient(this.baseUrl, this.tokens,
      {this.onUnauthorized, this.cache, this.offline});

  final String baseUrl;
  final TokenStore tokens;
  final ResponseCache? cache;
  final OfflineStatus? offline;

  void Function()? onUnauthorized;

  static const _timeout = Duration(seconds: 8);

  Future<Result<T>> send<T>(
    String method,
    String path, {
    Map<String, String>? query,
    Object? body,
    bool auth = true,
    int okStatus = 200,
    Duration timeout = _timeout,
    required T Function(Object? json) parse,
  }) async {
    var uri = Uri.parse('$baseUrl$path');
    if (query != null && query.isNotEmpty) {
      uri = uri.replace(queryParameters: query);
    }
    final cacheKey = method == 'GET' && cache != null ? uri.toString() : null;
    try {
      final headers = <String, String>{'Content-Type': 'application/json'};
      if (auth) {
        headers['Authorization'] = 'Bearer ${await tokens.read() ?? ''}';
      }
      final encoded = body == null ? null : jsonEncode(body);

      final res = await switch (method) {
        'GET' => http.get(uri, headers: headers),
        'POST' => http.post(uri, headers: headers, body: encoded),
        'PUT' => http.put(uri, headers: headers, body: encoded),
        'PATCH' => http.patch(uri, headers: headers, body: encoded),
        'DELETE' => http.delete(uri, headers: headers),
        _ => throw ArgumentError('Неизвестный метод $method'),
      }
          .timeout(timeout);

      if (auth && res.statusCode == 401) return Err(await _sessionDied());
      if (res.statusCode >= 500 && cacheKey != null) {
        final cached = await _fromCache(cacheKey, parse);
        if (cached != null) return cached;
      }
      if (res.statusCode < 500) offline?.online();
      if (res.statusCode != okStatus) return Err(apiMessage(res));

      if (res.statusCode == 204) return Ok(parse(null));
      final value = parse(jsonDecode(res.body));
      if (cacheKey != null) await cache!.write(cacheKey, res.body);
      return Ok(value);
    } on SocketException {
      return await _fromCache(cacheKey, parse) ??
          const Err('Нет сети — повторите попытку');
    } on http.ClientException {
      return await _fromCache(cacheKey, parse) ??
          const Err('Нет сети — повторите попытку');
    } on TimeoutException {
      return await _fromCache(cacheKey, parse) ?? const Err('Сервер не отвечает');
    } on FormatException {
      return const Err('Ответ не тот, что обещан');
    } on TypeError {
      return const Err('Ответ не тот, что обещан');
    }
  }

  Future<Result<T>?> _fromCache<T>(
    String? key,
    T Function(Object? json) parse,
  ) async {
    if (key == null) return null;
    final cached = await cache!.read(key);
    if (cached == null) return null;
    try {
      final value = parse(jsonDecode(cached.body));
      offline?.showingCached(cached.savedAt);
      return Ok(value, savedAt: cached.savedAt);
    } on FormatException {
      return null;
    } on TypeError {
      return null;
    }
  }

  Future<String> _sessionDied() async {
    await tokens.clear();
    onUnauthorized?.call();
    return 'Сессия истекла — войдите снова';
  }
}

List<T> pageItems<T>(
  Object? json,
  T Function(Map<String, dynamic> json) fromJson,
) =>
    ((json as Map<String, dynamic>)['items'] as List)
        .map((e) => fromJson(e as Map<String, dynamic>))
        .toList();
