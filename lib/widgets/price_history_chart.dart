// widgets/price_history_chart.dart
// Простая столбчатая диаграмма из Container-ов, без внешних пакетов.
import 'dart:math';
import 'package:flutter/material.dart';
import '../utils/formatters.dart';

class PriceHistoryChart extends StatelessWidget {
  final List<double> prices;
  final List<String> labels;

  const PriceHistoryChart({
    super.key,
    required this.prices,
    this.labels = const ['апр', 'май', 'июн', 'июл', 'авг', 'сен'],
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    final minPrice = prices.reduce(min);
    final range = prices.reduce(max) - minPrice;

    // Высота столбца: от 30 (минимум) до 100 (максимум).
    double barHeight(double price) =>
        range == 0 ? 60 : 30 + 70 * (price - minPrice) / range;

    return SizedBox(
      height: 150,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          for (var i = 0; i < prices.length; i++)
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    FittedBox(
                      child: Text(formatNumber(prices[i]),
                          style: text.labelSmall),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      height: barHeight(prices[i]),
                      decoration: BoxDecoration(
                        color: i == prices.length - 1
                            ? scheme.primary
                            : scheme.primaryContainer,
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(6)),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      i < labels.length ? labels[i] : '',
                      style: text.labelSmall
                          ?.copyWith(color: scheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
