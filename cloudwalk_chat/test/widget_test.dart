import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:cloudwalk_chat/main.dart';

void main() {
  testWidgets('app sobe e mostra AppBar', (tester) async {
    await tester.pumpWidget(const App());
    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.text('CloudWalk Chatbot'), findsOneWidget);
  });
}
