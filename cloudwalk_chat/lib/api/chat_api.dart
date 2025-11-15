import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatApi {
  final String base = const String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://127.0.0.1:8000',
  );

  Future<String> ask(String q, {String style = 'default'}) async {
    final uri = Uri.parse('$base/chat');

    final resp = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'question': q, 'style': style}),
        )
        .timeout(const Duration(seconds: 200)); // timeout duro do cliente

    if (resp.statusCode != 200) {
      throw 'HTTP ${resp.statusCode}: ${resp.body}';
    }

    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    final answer = (data['answer'] ?? '').toString();
    if (answer.isEmpty) throw 'Resposta vazia';
    return answer;
  }
}
