import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data/result.dart';
import '../data/sync_status.dart';
import '../models/catalog_model.dart';
import '../utils/formatters.dart';

class SyncCard extends StatefulWidget {
  const SyncCard({super.key});

  @override
  State<SyncCard> createState() => _SyncCardState();
}

class _SyncCardState extends State<SyncCard> {
  static const _pollEvery = Duration(seconds: 5);

  SyncStatus? _status;
  String? _error;
  bool _starting = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    final catalog = context.read<CatalogModel>();
    final result = await catalog.syncStatus();
    if (!mounted) return;
    final wasRunning = _status?.running ?? false;
    setState(() {
      switch (result) {
        case Ok(:final value):
          _status = value;
          _error = null;
        case Err(:final msg):
          _error = msg;
      }
    });
    final running = _status?.running ?? false;
    if (wasRunning && !running) catalog.load();
    _schedule();
  }

  void _schedule() {
    _timer?.cancel();
    if (_status?.running ?? false) {
      _timer = Timer(_pollEvery, _refresh);
    }
  }

  Future<void> _start() async {
    setState(() => _starting = true);
    final result = await context.read<CatalogModel>().startSync();
    if (!mounted) return;
    setState(() {
      _starting = false;
      switch (result) {
        case Ok(:final value):
          _status = value;
          _error = null;
        case Err(:final msg):
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(msg)));
      }
    });
    _schedule();
  }

  String _subtitle(SyncStatus status) {
    if (status.running) {
      return 'Идёт сбор цен со всех магазинов — это займёт 10–15 минут';
    }
    final last = status.lastSync;
    final lines = [
      'Последнее: ${last == null ? 'ещё не было' : formatSyncTime(last.toUtc().toIso8601String())}',
      if (status.enabled && status.nextAt != null)
        'Следующее: ${formatNextRun(status.nextAt!)}'
      else if (!status.enabled)
        'Автообновление выключено на сервере',
      if (status.failed) 'Прошлый сбор завершился с ошибкой',
    ];
    return lines.join('\n');
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final status = _status;
    final running = status?.running ?? false;

    return Card(
      color: scheme.secondaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            SizedBox(
              width: 32,
              height: 32,
              child: running
                  ? const Padding(
                      padding: EdgeInsets.all(4),
                      child: CircularProgressIndicator(strokeWidth: 3),
                    )
                  : Icon(Icons.schedule, color: scheme.onSecondaryContainer),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Обновление цен',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    status != null
                        ? _subtitle(status)
                        : (_error ?? 'Загрузка…'),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            FilledButton.tonal(
              onPressed: running || _starting || status == null ? null : _start,
              child: const Text('Обновить'),
            ),
          ],
        ),
      ),
    );
  }
}
