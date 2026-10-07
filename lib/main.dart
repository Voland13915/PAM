import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TechPrice',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        // Сине-зелёный: ассоциация с экономией и при этом нейтральный
        // к фирменным цветам магазинов (Bomba, Maximum и др.).
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00796B),
        ),
        textTheme: const TextTheme(
          titleLarge: TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      home: const Scaffold(body: Center(child: Text('TechPrice'))),
    );
  }
}