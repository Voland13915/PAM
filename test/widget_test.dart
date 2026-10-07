// test/widget_test.dart — заменяет тест-счётчик из шаблона flutter create
import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/main.dart';

void main() {
  testWidgets('Стартовое меню показывает экраны', (tester) async {
    await tester.pumpWidget(const MyApp());
    expect(find.text('Каталог'), findsOneWidget);
    expect(find.text('Профиль'), findsOneWidget);
  });
}
