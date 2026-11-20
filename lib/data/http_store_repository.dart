import 'api_client.dart';
import 'result.dart';
import 'store.dart';
import 'store_repository.dart';
import 'sync_status.dart';

class HttpStoreRepository implements StoreRepository {
  HttpStoreRepository(this._api);

  final ApiClient _api;

  @override
  Future<Result<List<Store>>> fetchAll() => _api.send(
        'GET',
        '/stores',
        query: {'limit': '100'},
        parse: (json) => pageItems(json, Store.fromJson),
      );

  @override
  Future<Result<SyncStatus>> fetchSync() => _api.send(
        'GET',
        '/sync',
        parse: (json) => SyncStatus.fromJson(json as Map<String, dynamic>),
      );

  @override
  Future<Result<SyncStatus>> startSync() => _api.send(
        'POST',
        '/sync',
        okStatus: 202,
        parse: (json) => SyncStatus.fromJson(json as Map<String, dynamic>),
      );
}
