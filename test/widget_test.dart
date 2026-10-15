import 'package:flutter_test/flutter_test.dart';
import 'package:tech_price/main.dart';

void main() {
  testWidgets('Приложение стартует на экране входа', (tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();
    expect(find.text('Войти'), findsOneWidget);
  });

  testWidgets('Пустой вход показывает ошибки', (tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Войти'));
    await tester.pump();
    expect(find.text('Введите e-mail'), findsOneWidget);
    expect(find.text('Введите пароль'), findsOneWidget);
  });
}
