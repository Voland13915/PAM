import 'catalog_facets.dart';
import 'catalog_filter.dart';
import 'product.dart';
import 'result.dart';

abstract class ProductRepository {
  Future<Result<List<Product>>> fetchAll({
    int page = 1,
    int limit = 20,
    String? search,
    CatalogFilter filter = const CatalogFilter(),
  });
  Future<Result<CatalogFacets>> fetchFacets({
    String? search,
    CatalogFilter filter = const CatalogFilter(),
  });
  Future<Result<Product>> fetchById(int id);
  Future<Result<List<String>>> fetchImages(int id);
  Future<Result<Product>> create(Product product);
  Future<Result<Product>> update(Product product);
  Future<Result<void>> delete(int id);
}
