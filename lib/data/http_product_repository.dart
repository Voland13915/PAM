import 'api_client.dart';
import 'product.dart';
import 'product_repository.dart';
import 'result.dart';

class HttpProductRepository implements ProductRepository {
  HttpProductRepository(this._api);

  final ApiClient _api;

  Product _product(Object? json) =>
      Product.fromJson(json as Map<String, dynamic>);

  @override
  Future<Result<List<Product>>> fetchAll({
    int page = 1,
    int limit = 20,
    String? search,
  }) =>
      _api.send(
        'GET',
        '/products',
        query: {
          'page': '$page',
          'limit': '$limit',
          if (search != null && search.isNotEmpty) 'search': search,
        },
        parse: (json) => pageItems(json, Product.fromJson),
      );

  @override
  Future<Result<Product>> fetchById(int id) =>
      _api.send('GET', '/products/$id', parse: _product);

  @override
  Future<Result<Product>> create(Product product) => _api.send(
        'POST',
        '/products',
        body: product.toJson(),
        okStatus: 201,
        parse: _product,
      );

  @override
  Future<Result<Product>> update(Product product) => _api.send(
        'PUT',
        '/products/${product.id}',
        body: product.toJson(),
        parse: _product,
      );

  @override
  Future<Result<void>> delete(int id) => _api.send(
        'DELETE',
        '/products/$id',
        okStatus: 204,
        parse: (_) {},
      );
}
