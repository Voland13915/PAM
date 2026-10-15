import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import '../data/mock_data.dart';
import '../utils/formatters.dart';
import '../utils/validators.dart';

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

  @override
  void dispose() {
    _priceCtrl.dispose();
    super.dispose();
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    final price = double.parse(_priceCtrl.text);
    final store = storeById(_storeId!).name;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Слежение включено: до ${formatPrice(price)} в $store'),
      ),
    );
    context.pop(); // открыто push-ем → закрывается pop-ом
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    // Экран сам ищет товар по id из адреса.
    final product = productById(widget.productId);
    final best = product.bestOffer.price;

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
                      '${storeById(offer.storeId).name} — '
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
              onPressed: _save,
              child: const Text('Сохранить'),
            ),
          ],
        ),
      ),
    );
  }
}
