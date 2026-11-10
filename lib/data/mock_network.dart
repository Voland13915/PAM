class MockNetwork {
  MockNetwork({this.latency = const Duration(milliseconds: 800)});

  final Duration latency;

  bool simulateError = false;

  static const errorMessage = 'Сервер не отвечает — повторите попытку';

  Future<String?> roundTrip() async {
    await Future.delayed(latency);
    return simulateError ? errorMessage : null;
  }
}
