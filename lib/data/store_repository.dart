// data/store_repository.dart — справочник магазинов: только чтение.
import 'result.dart';
import 'store.dart';

abstract class StoreRepository {
  Future<Result<List<Store>>> fetchAll(); // L5: GET /stores
}
