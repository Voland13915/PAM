import 'api_client.dart';
import 'auth_user.dart';
import 'result.dart';
import 'token_store.dart';

class AuthApi {
  AuthApi(this._api, this._tokens);

  final ApiClient _api;
  final TokenStore _tokens;

  Future<Result<AuthUser>> register(
          String email, String password, String name) =>
      _authorize('/auth/register',
          {'email': email, 'password': password, 'name': name}, 201);

  Future<Result<AuthUser>> login(String email, String password) =>
      _authorize('/auth/login', {'email': email, 'password': password}, 200);

  Future<Result<AuthUser>> me() => _api.send(
        'GET',
        '/me',
        timeout: const Duration(seconds: 3),
        parse: (json) => AuthUser.fromJson(json as Map<String, dynamic>),
      );

  Future<void> logout() => _tokens.clear();

  Future<Result<AuthUser>> _authorize(
      String path, Map<String, Object?> body, int okStatus) async {
    final result = await _api.send(
      'POST',
      path,
      body: body,
      auth: false,
      okStatus: okStatus,
      parse: (json) {
        final data = json as Map<String, dynamic>;
        return (
          data['token'] as String,
          AuthUser.fromJson(data['user'] as Map<String, dynamic>),
        );
      },
    );
    switch (result) {
      case Ok(:final value):
        await _tokens.save(value.$1);
        return Ok(value.$2);
      case Err(:final msg):
        return Err(msg);
    }
  }
}
