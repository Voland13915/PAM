import 'mock_data.dart';
import 'mock_network.dart';
import 'product.dart';
import 'product_repository.dart';
import 'result.dart';

class MockProductRepository implements ProductRepository {
  MockProductRepository(this._network);

  final MockNetwork _network;
  final List<Product> _products = List.of(mockProducts); // seed из L2
  int _nextId = 1000;

  static const _notFound = 'Товар не существует';

  @override
  Future<Result<List<Product>>> fetchAll() async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    return Ok(List.of(_products));
  }

  @override
  Future<Result<Product>> fetchById(int id) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final index = _products.indexWhere((p) => p.id == id);
    if (index == -1) return const Err(_notFound); // «404» mock-а
    return Ok(_products[index]);
  }

  @override
  Future<Result<Product>> create(Product product) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final created = product.copyWith(id: _nextId++);
    _products.add(created);
    return Ok(created);
  }

  @override
  Future<Result<Product>> update(Product product) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final index = _products.indexWhere((p) => p.id == product.id);
    if (index == -1) return const Err(_notFound);
    _products[index] = product;
    return Ok(product);
  }

  @override
  Future<Result<void>> delete(int id) async {
    final failure = await _network.roundTrip();
    if (failure != null) return Err(failure);
    final before = _products.length;
    _products.removeWhere((p) => p.id == id);
    if (_products.length == before) return const Err(_notFound);
    return const Ok(null);
  }
}
