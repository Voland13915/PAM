// data/mock_network.dart — «повадки сети» для всех mock-хранилищ:
// задержка и переключаемая авария. Один объект на все mock-и, поэтому
// один переключатель в профиле роняет весь «backend» сразу.
// Леса L4: исчезает на L5 вместе с mock-ами.

class MockNetwork {
  MockNetwork({this.latency = const Duration(milliseconds: 800)});

  final Duration latency;

  /// Авария: включена → любой вызов любого mock-хранилища проваливается.
  bool simulateError = false;

  static const errorMessage = 'Сервер не отвечает — повторите попытку';

  /// Пролог каждого метода mock-а: ждём, как настоящая сеть,
  /// затем либо сообщение об аварии, либо null (можно продолжать).
  Future<String?> roundTrip() async {
    await Future.delayed(latency); // без задержки нет состояния «грузится»
    return simulateError ? errorMessage : null;
  }
}
