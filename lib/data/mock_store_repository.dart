// data/mock_store_repository.dart — справочник магазинов в памяти.
import 'mock_data.dart';
import 'mock_network.dart';
import 'result.dart';
import 'store.dart';
import 'store_repository.dart';

class MockStoreRepository implements StoreRepository {
  MockStoreRepository(this._network);

  final MockNetwork _network;
  final List<Store> _stores = List.of(mockStores);

  @override
  Future<Result<List<Store>>> fetchAll() async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    return Ok(List.of(_stores));
  }
}
