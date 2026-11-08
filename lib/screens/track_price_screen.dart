import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/wishlist_item.dart';
import '../models/catalog_model.dart';
import '../models/wishlist_model.dart';
import '../utils/formatters.dart';
import '../utils/validators.dart';
import '../widgets/missing_product_view.dart';

class TrackPriceScreen extends StatefulWidget {
  final int productId;

  const TrackPriceScreen({super.key, required this.productId});

  @override
  State<TrackPriceScreen> createState() => _TrackPriceScreenState();
}

class _TrackPriceScreenState extends State<TrackPriceScreen> {
  final _formKey = GlobalKey<FormState>();
  final _priceCtrl = TextEditingController();
  int? _storeId;
  bool _notify = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final existing =
        context.read<WishlistModel>().byProduct(widget.productId);
    if (existing != null) {
      _priceCtrl.text = existing.targetPrice.round().toString();
      _storeId = existing.storeId;
      _notify = existing.notify;
    }
  }

  @override
  void dispose() {
    _priceCtrl.dispose();
    super.dispose();
  }

  Future<void> _save(String storeName) async {
    if (!_formKey.currentState!.validate()) return;

    final wishlist = context.read<WishlistModel>();
    final existing = wishlist.byProduct(widget.productId);
    final price = double.parse(_priceCtrl.text);

    setState(() => _saving = true);
    final error = existing == null
        ? await wishlist.add(WishlistItem(
            0,
            widget.productId,
            _storeId!,
            price,
            notify: _notify,
          ))
        : await wishlist.update(existing.copyWith(
            storeId: _storeId,
            targetPrice: price,
            notify: _notify,
          ));
    if (!mounted) return;
    setState(() => _saving = false);

    if (error != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error)));
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Слежение включено: до ${formatPrice(price)} '
            'в $storeName'),
      ),
    );
    context.pop();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final catalog = context.watch<CatalogModel>();
    final product = catalog.byId(widget.productId);
    if (product == null) {
      return const MissingProductView(title: 'Следить за ценой');
    }
    final best = product.bestOffer.price;
    final storeName = _storeId == null ? '' : catalog.storeName(_storeId!);

    return Scaffold(
      appBar: AppBar(title: const Text('Следить за ценой')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(product.name, style: text.titleMedium),
            const SizedBox(height: 4),
            Text(
              'Сейчас лучшая цена: ${formatPrice(best)}',
              style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _priceCtrl,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              textInputAction: TextInputAction.done,
              decoration: const InputDecoration(
                labelText: 'Желаемая цена, MDL',
                helperText: 'Должна быть ниже текущей лучшей цены',
                prefixIcon: Icon(Icons.price_change_outlined),
                border: OutlineInputBorder(),
              ),
              validator: (value) => validateTargetPrice(value, best),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<int>(
              initialValue: _storeId,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Магазин',
                prefixIcon: Icon(Icons.storefront_outlined),
                border: OutlineInputBorder(),
              ),
              items: [
                for (final offer in product.inStockOffers)
                  DropdownMenuItem(
                    value: offer.storeId,
                    child: Text(
                      '${catalog.storeName(offer.storeId)} — '
                      '${formatPrice(offer.price)}',
                    ),
                  ),
              ],
              onChanged: (value) => setState(() => _storeId = value),
              validator: (value) => value == null ? 'Выберите магазин' : null,
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Уведомить, когда цена снизится'),
              value: _notify,
              onChanged: (value) => setState(() => _notify = value),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _saving ? null : () => _save(storeName),
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Сохранить'),
            ),
          ],
        ),
      ),
    );
  }
}
