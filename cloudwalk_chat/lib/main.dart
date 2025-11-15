import 'package:flutter/material.dart';
import 'pages/chat_page.dart';

void main() => runApp(const App());

class App extends StatelessWidget {
  const App({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'CloudWalk Chat',
      theme: ThemeData(useMaterial3: true),
      home: const ChatPage(),
    );
  }
}
