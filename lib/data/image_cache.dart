import 'package:flutter_cache_manager/flutter_cache_manager.dart';

final productImages = CacheManager(
  Config(
    'product_images',
    stalePeriod: const Duration(days: 30),
    maxNrOfCacheObjects: 3000,
  ),
);
