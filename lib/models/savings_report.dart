import '../data/product.dart';
import 'app_settings.dart';

class ItemSaving {
  final Product product;
  final Offer best;
  final Offer highest;
  final double average;
  final int stores;

  const ItemSaving({
    required this.product,
    required this.best,
    required this.highest,
    required this.average,
    required this.stores,
  });

  factory ItemSaving.of(Product product) {
    final offers = product.inStockOffers;
    var best = offers.first;
    var highest = offers.first;
    var sum = 0.0;
    for (final o in offers) {
      if (o.price < best.price) best = o;
      if (o.price > highest.price) highest = o;
      sum += o.price;
    }
    return ItemSaving(
      product: product,
      best: best,
      highest: highest,
      average: sum / offers.length,
      stores: offers.length,
    );
  }

  double base(SavingsBaseline baseline) =>
      baseline == SavingsBaseline.highest ? highest.price : average;

  double saving(SavingsBaseline baseline) => base(baseline) - best.price;

  double percent(SavingsBaseline baseline) {
    final value = base(baseline);
    return value <= 0 ? 0 : saving(baseline) / value * 100;
  }

  double get discount {
    final old = best.oldPrice;
    return old != null && old > best.price ? old - best.price : 0;
  }

  bool get comparable => stores > 1;
}

class StoreSaving {
  final int storeId;
  final List<ItemSaving> items;

  const StoreSaving(this.storeId, this.items);

  double get total => items.fold(0, (sum, i) => sum + i.best.price);

  double saving(SavingsBaseline baseline) =>
      items.fold(0, (sum, i) => sum + i.saving(baseline));
}

class CategorySaving {
  final String category;
  final int count;
  final double saving;

  const CategorySaving(this.category, this.count, this.saving);
}

class SavingsReport {
  final List<ItemSaving> items;
  final List<Product> unavailable;

  const SavingsReport._(this.items, this.unavailable);

  factory SavingsReport.of(Iterable<Product> products) {
    final items = <ItemSaving>[];
    final unavailable = <Product>[];
    for (final p in products) {
      if (p.isAvailable) {
        items.add(ItemSaving.of(p));
      } else {
        unavailable.add(p);
      }
    }
    return SavingsReport._(items, unavailable);
  }

  bool get isEmpty => items.isEmpty && unavailable.isEmpty;

  double get bestTotal => items.fold(0, (sum, i) => sum + i.best.price);

  double get averageTotal => items.fold(0, (sum, i) => sum + i.average);

  double get highestTotal => items.fold(0, (sum, i) => sum + i.highest.price);

  double baseTotal(SavingsBaseline baseline) =>
      baseline == SavingsBaseline.highest ? highestTotal : averageTotal;

  double saving(SavingsBaseline baseline) =>
      baseTotal(baseline) - bestTotal;

  double percent(SavingsBaseline baseline) {
    final base = baseTotal(baseline);
    return base <= 0 ? 0 : saving(baseline) / base * 100;
  }

  double get discounts => items.fold(0, (sum, i) => sum + i.discount);

  int get singleStore => items.where((i) => !i.comparable).length;

  List<ItemSaving> ranked(SavingsBaseline baseline) => [...items]
    ..sort((a, b) => b.saving(baseline).compareTo(a.saving(baseline)));

  List<StoreSaving> byStore(SavingsBaseline baseline) {
    final groups = <int, List<ItemSaving>>{};
    for (final i in items) {
      groups.putIfAbsent(i.best.storeId, () => []).add(i);
    }
    return [
      for (final e in groups.entries) StoreSaving(e.key, e.value),
    ]..sort((a, b) {
        final bySaving = b.saving(baseline).compareTo(a.saving(baseline));
        return bySaving != 0 ? bySaving : b.items.length - a.items.length;
      });
  }

  List<CategorySaving> byCategory(SavingsBaseline baseline) {
    final counts = <String, int>{};
    final sums = <String, double>{};
    for (final i in items) {
      final c = i.product.category;
      counts[c] = (counts[c] ?? 0) + 1;
      sums[c] = (sums[c] ?? 0) + i.saving(baseline);
    }
    return [
      for (final c in counts.keys) CategorySaving(c, counts[c]!, sums[c]!),
    ]..sort((a, b) => b.saving.compareTo(a.saving));
  }
}
