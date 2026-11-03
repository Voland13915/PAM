// models/shopping_list_model.dart — список покупок (аналог корзины с C7):
// разделяемое состояние в памяти, без хранилища. Пишут детали товара,
// читают вкладка «Покупки», badge на панели и профиль.
import 'package:flutter/foundation.dart';

class ShoppingListModel extends ChangeNotifier {
  final List<int> _productIds = [];

  List<int> get productIds => List.unmodifiable(_productIds);
  int get count => _productIds.length;
  bool contains(int productId) => _productIds.contains(productId);

  void add(int productId) {
    if (_productIds.contains(productId)) return; // уже есть — мутации нет
    _productIds.add(productId);
    notifyListeners(); // весть уходит ко ВСЕМ подписчикам
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
