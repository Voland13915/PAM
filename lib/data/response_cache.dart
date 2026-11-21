import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

class CachedResponse {
  final String body;
  final DateTime savedAt;

  const CachedResponse(this.body, this.savedAt);
}

class ResponseCache {
  ResponseCache({
    Future<Directory> Function()? directory,
    this.maxAge = const Duration(days: 7),
    DateTime Function()? clock,
  })  : _directory = directory ?? _defaultDirectory,
        _clock = clock ?? DateTime.now;

  final Future<Directory> Function() _directory;
  final DateTime Function() _clock;
  final Duration maxAge;
  Directory? _dir;

  static Future<Directory> _defaultDirectory() async =>
      Directory('${(await getApplicationSupportDirectory()).path}/api_cache');

  Future<Directory> _folder() async {
    final dir = _dir ??= await _directory();
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  static String fileName(String key) {
    var a = 0x811c9dc5;
    var b = 0x01000193;
    for (final unit in utf8.encode(key)) {
      a = ((a ^ unit) * 0x01000193) & 0xffffffff;
      b = ((b ^ unit) * 0x811c9dc5 + 7) & 0xffffffff;
    }
    return '${a.toRadixString(16).padLeft(8, '0')}'
        '${b.toRadixString(16).padLeft(8, '0')}.json';
  }

  Future<File> _file(String key) async =>
      File('${(await _folder()).path}/${fileName(key)}');

  Future<void> write(String key, String body) async {
    try {
      final file = await _file(key);
      final temp = File('${file.path}.tmp');
      await temp.writeAsString(jsonEncode({
        'key': key,
        'savedAt': _clock().toIso8601String(),
        'body': body,
      }));
      await temp.rename(file.path);
    } on FileSystemException {
      return;
    }
  }

  Future<CachedResponse?> read(String key) async {
    try {
      final file = await _file(key);
      if (!await file.exists()) return null;
      final data = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      if (data['key'] != key) return null;
      final savedAt = DateTime.parse(data['savedAt'] as String);
      if (_clock().difference(savedAt) > maxAge) return null;
      return CachedResponse(data['body'] as String, savedAt);
    } on FileSystemException {
      return null;
    } on FormatException {
      return null;
    } on TypeError {
      return null;
    }
  }

  Future<void> prune() async {
    try {
      final dir = await _folder();
      final limit = _clock().subtract(maxAge);
      await for (final entity in dir.list()) {
        if (entity is File && (await entity.lastModified()).isBefore(limit)) {
          await entity.delete();
        }
      }
    } on FileSystemException {
      return;
    }
  }

  Future<void> clear() async {
    try {
      final dir = await _folder();
      await dir.delete(recursive: true);
    } on FileSystemException {
      return;
    }
  }
}
