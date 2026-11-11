import 'api_client.dart';
import 'result.dart';
import 'store.dart';
import 'store_repository.dart';

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
}
