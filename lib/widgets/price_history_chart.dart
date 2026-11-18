import 'dart:math';
import 'package:flutter/material.dart';
import '../utils/formatters.dart';

class PriceHistoryChart extends StatelessWidget {
  final List<double> prices;

  final List<DateTime> dates;

  const PriceHistoryChart({
    super.key,
    required this.prices,
    this.dates = const [],
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    if (prices.isEmpty) {
      return Text('История цены появится после следующего обновления',
          style: text.bodyMedium?.copyWith(color: scheme.onSurfaceVariant));
    }

    final minPrice = prices.reduce(min);
    final range = prices.reduce(max) - minPrice;

    double barHeight(double price) =>
        range == 0 ? 55 : 30 + 60 * (price - minPrice) / range;

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
                      fit: BoxFit.scaleDown,
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
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        i < dates.length ? formatShortDate(dates[i]) : '',
                        maxLines: 1,
                        softWrap: false,
                        style: text.labelSmall
                            ?.copyWith(color: scheme.onSurfaceVariant),
                      ),
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
