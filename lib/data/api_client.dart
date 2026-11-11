import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'api_message.dart';
import 'result.dart';
import 'token_store.dart';

class ApiClient {
  ApiClient(this.baseUrl, this.tokens, {this.onUnauthorized});

  final String baseUrl;
  final TokenStore tokens;

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
    try {
      var uri = Uri.parse('$baseUrl$path');
      if (query != null && query.isNotEmpty) {
        uri = uri.replace(queryParameters: query);
      }
      final headers = <String, String>{'Content-Type': 'application/json'};
      if (auth) {
        headers['Authorization'] = 'Bearer ${await tokens.read() ?? ''}';
      }
      final encoded = body == null ? null : jsonEncode(body);

      final res = await switch (method) {
        'GET' => http.get(uri, headers: headers),
        'POST' => http.post(uri, headers: headers, body: encoded),
        'PUT' => http.put(uri, headers: headers, body: encoded),
        'DELETE' => http.delete(uri, headers: headers),
        _ => throw ArgumentError('Неизвестный метод $method'),
      }
          .timeout(timeout);

      if (auth && res.statusCode == 401) return Err(await _sessionDied());
      if (res.statusCode != okStatus) return Err(apiMessage(res));

      if (res.statusCode == 204) return Ok(parse(null));
      return Ok(parse(jsonDecode(res.body)));
    } on SocketException {
      return const Err('Нет сети — повторите попытку');
    } on http.ClientException {
      return const Err('Нет сети — повторите попытку');
    } on TimeoutException {
      return const Err('Сервер не отвечает');
    } on FormatException {
      return const Err('Ответ не тот, что обещан');
    } on TypeError {
      return const Err('Ответ не тот, что обещан');
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
