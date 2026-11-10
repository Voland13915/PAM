import 'package:flutter/foundation.dart';

class ShoppingListModel extends ChangeNotifier {
  final List<int> _productIds = [];

  List<int> get productIds => List.unmodifiable(_productIds);
  int get count => _productIds.length;
  bool contains(int productId) => _productIds.contains(productId);

  void add(int productId) {
    if (_productIds.contains(productId)) return;
    _productIds.add(productId);
    notifyListeners();
  }

  void remove(int productId) {
    if (!_productIds.remove(productId)) return;
    notifyListeners();
  }

  void clear() {
    if (_productIds.isEmpty) return;
    _productIds.clear();
    notifyListeners();
  }
}
