import 'product.dart';
import 'result.dart';

abstract class ProductRepository {
  Future<Result<List<Product>>> fetchAll({
    int page = 1,
    int limit = 20,
    String? search,
  });
  Future<Result<Product>> fetchById(int id);
  Future<Result<Product>> create(Product product);
  Future<Result<Product>> update(Product product);
  Future<Result<void>> delete(int id);
}
