import 'result.dart';
import 'store.dart';
import 'sync_status.dart';

abstract class StoreRepository {
  Future<Result<List<Store>>> fetchAll();
  Future<Result<SyncStatus>> fetchSync();
  Future<Result<SyncStatus>> startSync();
}
