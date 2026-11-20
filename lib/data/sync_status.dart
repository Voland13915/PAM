class SyncStatus {
  final bool enabled;
  final bool running;
  final DateTime? nextAt;
  final DateTime? lastSync;
  final DateTime? finishedAt;
  final int? exitCode;

  const SyncStatus({
    this.enabled = false,
    this.running = false,
    this.nextAt,
    this.lastSync,
    this.finishedAt,
    this.exitCode,
  });

  static DateTime? _time(Object? value) =>
      value is String ? DateTime.tryParse(value)?.toLocal() : null;

  factory SyncStatus.fromJson(Map<String, dynamic> j) => SyncStatus(
        enabled: j['enabled'] as bool? ?? false,
        running: j['running'] as bool? ?? false,
        nextAt: _time(j['nextAt']),
        lastSync: _time(j['lastSync']),
        finishedAt: _time(j['finishedAt']),
        exitCode: j['exitCode'] as int?,
      );

  bool get failed => !running && exitCode != null && exitCode != 0;
}
