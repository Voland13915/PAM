class AuthUser {
  final int id;
  final String email;
  final String name;

  const AuthUser(this.id, this.email, this.name);

  factory AuthUser.fromJson(Map<String, dynamic> j) => AuthUser(
        j['id'] as int,
        j['email'] as String,
        j['name'] as String,
      );
}
