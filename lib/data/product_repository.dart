// data/product_repository.dart — контракт: ЧТО можно просить, а не КАК.
// На L5 каждый метод = один REST-вызов, экраны не меняются.
import 'product.dart';
import 'result.dart';

abstract class ProductRepository {
  Future<Result<List<Product>>> fetchAll(); //  L5: GET    /products
  Future<Result<Product>> fetchById(int id); // L5: GET    /products/{id}
  Future<Result<Product>> create(Product product); // POST   /products
  Future<Result<Product>> update(Product product); // PUT    /products/{id}
  Future<Result<void>> delete(int id); //       L5: DELETE /products/{id}
}
