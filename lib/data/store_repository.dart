import 'result.dart';
import 'store.dart';

abstract class StoreRepository {
  Future<Result<List<Store>>> fetchAll();
}
