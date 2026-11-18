import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/widgets/price_history_chart.dart';

const _nbsp = '\u00A0';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  testWidgets('Неизменная цена показывается текстом, а не одним столбиком',
      (tester) async {
    await tester.pumpWidget(_wrap(PriceHistoryChart(
      prices: const [14999, 14999],
      dates: [DateTime(2026, 11, 18), DateTime(2026, 11, 20)],
    )));

    expect(find.text('Цена не менялась с 18$_nbspноя: 14${_nbsp}999${_nbsp}MDL'),
        findsOneWidget);
  });

  testWidgets('Изменения цены рисуются столбиками с датами', (tester) async {
    await tester.pumpWidget(_wrap(PriceHistoryChart(
      prices: const [15999, 14999],
      dates: [DateTime(2026, 11, 18), DateTime(2026, 11, 20)],
    )));

    expect(find.text('18$_nbspноя'), findsOneWidget);
    expect(find.text('20$_nbspноя'), findsOneWidget);
    expect(find.textContaining('не менялась'), findsNothing);
  });
}
