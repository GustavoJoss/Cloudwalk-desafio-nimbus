import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/chat_api.dart';
import '../models/message.dart';
import '../theme.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});
  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  Future<void> _openLink(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  /// Remove a seção "Fontes:" do markdown para não duplicar links
  String _stripSourcesSection(String? md) {
    final text = (md ?? '');
    final i = text.toLowerCase().indexOf('fontes:');
    return i >= 0 ? text.substring(0, i).trimRight() : text;
  }

  /// Extrai URLs, limpa pontuação final e deduplica. Aceita String? (defensivo).
  List<Uri> _extractSources(String? md) {
    final text = (md ?? '').trim();
    if (text.isEmpty) return const <Uri>[];

    // tenta focar só na seção "Fontes:"
    final i = text.toLowerCase().indexOf('fontes:');
    final slice = i >= 0 ? text.substring(i) : text;

    // RegExp local (evita referência quebrada em hot-reload no web)
    final re = RegExp(r'(https?://[^\s)]+)', multiLine: true);

    final raw = re
        .allMatches(slice)
        .map((m) => m.group(0) ?? '')
        .map((s) => s.replaceFirst(RegExp(r'[)\].,;:]+$'), ''))
        .map(Uri.tryParse)
        .whereType<Uri>()
        .toList(growable: false);

    // deduplica
    final seen = <String>{};
    return raw.where((u) => seen.add(u.toString())).toList(growable: false);
  }

  List<Widget> _buildSourceChips(List<Uri> sources) {
    if (sources.isEmpty) return const <Widget>[];
    return <Widget>[
      const SizedBox(height: 8),
      Wrap(
        spacing: 6,
        runSpacing: 6,
        children: [
          for (final u in sources.take(6))
            InputChip(
              avatar: const Icon(
                Icons.link,
                size: 16,
                color: AppColors.primary,
              ),
              label: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 220),
                child: Text(
                  u.host,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: AppColors.primary,
                  ),
                ),
              ),
              tooltip: u.toString(),
              backgroundColor: const Color(0xFFEFEAFF),
              side: const BorderSide(color: Color(0xFFDCD4FF)),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              visualDensity: VisualDensity.compact,
              onPressed: () => _openLink(u.toString()),
            ),
          if (sources.length > 6)
            InputChip(
              label: Text(
                '+${sources.length - 6}',
                style: const TextStyle(
                  fontSize: 12.5,
                  color: AppColors.primary,
                ),
              ),
              backgroundColor: const Color(0xFFF6F3FF),
              side: const BorderSide(color: Color(0xFFE6E0FF)),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              visualDensity: VisualDensity.compact,
              onPressed: () => _openLink(sources[6].toString()),
            ),
        ],
      ),
    ];
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Resposta copiada')));
  }

  // Estado do chat

  final TextEditingController _input = TextEditingController(
    text: 'O que é a CloudWalk e qual a relação com a InfinitePay?',
  );
  final ChatApi _api = ChatApi();
  final List<Message> _messages = [];
  final ScrollController _scroll = ScrollController();

  bool _loading = false;

  // efeito de digitação
  Timer? _typingTimer;
  int _typingIndex = 0;
  String _typingFullText = '';
  int _botMessageIdx = -1;

  // velocidade (ms) – menor = mais rápido
  static const int _typingSpeedMs = 22;
  // limites de segurança do efeito de digitação
  static const int _typingMaxMillis = 30 * 1000; // 30s máximo "digitando"
  static const int _answerMaxChars = 4000; // corta respostas muito longas

  @override
  void dispose() {
    _typingTimer?.cancel();
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final q = _input.text.trim();
    if (q.isEmpty || _loading) return;

    _stopTyping();

    setState(() {
      _loading = true;
      _messages.add(Message(Sender.user, q));
      _input.clear();
    });
    _scrollToEnd();

    try {
      final answer = await _api.ask(q, style: 'friendly');
      _startTyping(answer);
    } catch (e) {
      setState(() => _messages.add(Message(Sender.bot, 'Erro: $e')));
    } finally {
      setState(() => _loading = false);
    }
  }

  void _startTyping(String answer) {
    _stopTyping(); // cancela qualquer sessão anterior

    // limita tamanho da resposta para evitar loops grandes
    _typingFullText = answer.length > _answerMaxChars
        ? answer.substring(0, _answerMaxChars)
        : answer;

    _typingIndex = 0;
    _botMessageIdx = _messages.length;
    _messages.add(Message(Sender.bot, ''));

    final startedAt = DateTime.now();

    _typingTimer = Timer.periodic(
      const Duration(milliseconds: _typingSpeedMs),
      (t) {
        // se ultrapassar o tempo máximo, revela tudo e encerra
        if (DateTime.now().difference(startedAt).inMilliseconds >
            _typingMaxMillis) {
          setState(() {
            _messages[_botMessageIdx] = Message(Sender.bot, _typingFullText);
          });
          _stopTyping();
          return;
        }

        if (_typingIndex >= _typingFullText.length) {
          _stopTyping();
          return;
        }

        setState(() {
          final next = _typingFullText.substring(0, _typingIndex + 1);
          _messages[_botMessageIdx] = Message(Sender.bot, next);
          _typingIndex++;
        });
        _scrollToEnd();
      },
    );
  }

  void _stopTyping() {
    _typingTimer?.cancel();
    _typingTimer = null;
    _typingIndex = 0;
    _typingFullText = '';
    _botMessageIdx = -1;
  }

  void _revealAllNow() {
    if (_typingTimer == null || _botMessageIdx < 0) return;
    setState(() {
      _messages[_botMessageIdx] = Message(Sender.bot, _typingFullText);
    });
    _stopTyping();
    _scrollToEnd();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent + 120,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  Widget _typingDots() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (i) {
        final delay = i * 120;
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 2),
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: 0.3, end: 1),
            duration: Duration(milliseconds: 600 + delay),
            curve: Curves.easeInOut,
            builder: (_, value, __) => Opacity(
              opacity: value,
              child: const CircleAvatar(
                radius: 3.2,
                backgroundColor: AppColors.primary,
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _bubble(Message m) {
    final isUser = m.from == Sender.user;

    if (isUser) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 6),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.primary,
              borderRadius: BorderRadius.circular(14),
            ),
            child: SelectableText(
              m.text,
              style: const TextStyle(color: Colors.white, height: 1.32),
            ),
          ),
        ],
      );
    }

    // Pré-calcula fontes e texto sem a seção "Fontes:"
    final sources = _extractSources(m.text);
    final mdData = _stripSourcesSection(m.text);
    final mdToRender = (mdData.isEmpty) ? ' ' : mdData;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
          decoration: BoxDecoration(
            color: AppColors.bubbleBot,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE8E4FF)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Conteúdo em Markdown + chips de fontes
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    MarkdownBody(
                      data: mdToRender,
                      selectable: true,
                      softLineBreak: true,
                      onTapLink: (text, href, title) {
                        if (href != null) _openLink(href);
                      },
                      styleSheet:
                          MarkdownStyleSheet.fromTheme(
                            Theme.of(context),
                          ).copyWith(
                            p: const TextStyle(
                              color: AppColors.textPrimary,
                              height: 1.35,
                              fontSize: 15.5,
                            ),
                            h1: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                            h2: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                            h3: const TextStyle(
                              fontSize: 16.5,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                            listBullet: const TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 16,
                            ),
                            a: const TextStyle(
                              color: AppColors.primary,
                              decoration: TextDecoration.underline,
                            ),
                            code: const TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 14.5,
                              color: AppColors.textPrimary,
                            ),
                            codeblockDecoration: BoxDecoration(
                              color: const Color(0xFFF6F4FF),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: const Color(0xFFE6E0FF),
                              ),
                            ),
                            blockquoteDecoration: BoxDecoration(
                              color: const Color(0xFFF7F5FF),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: const Color(0xFFEDE9FF),
                              ),
                            ),
                          ),
                    ),
                    ..._buildSourceChips(sources),
                  ],
                ),
              ),

              // Botão copiar
              IconButton(
                tooltip: 'Copiar',
                onPressed: m.text.trim().isEmpty
                    ? null
                    : () => _copyToClipboard(m.text),
                icon: const Icon(
                  Icons.copy_rounded,
                  size: 18,
                  color: AppColors.primary,
                ),
                splashRadius: 18,
                padding: const EdgeInsets.only(left: 6, top: 2),
                constraints: const BoxConstraints(),
              ),
            ],
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final typing = _typingTimer != null;
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CloudWalk Chatbot'),
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        actions: [
          if (typing)
            TextButton(
              onPressed: _revealAllNow,
              child: const Text(
                'Pular',
                style: TextStyle(color: AppColors.primary),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // barra colorida no topo
          Container(
            height: 4,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [scheme.primary, AppColors.accent],
              ),
            ),
          ),
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + (typing ? 1 : 0),
              itemBuilder: (_, i) {
                if (typing && i == _messages.length) {
                  // item extra mostrando “digitando…”
                  return Align(
                    alignment: Alignment.centerLeft,
                    child: Container(
                      margin: const EdgeInsets.symmetric(vertical: 6),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.bubbleBot,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFE8E4FF)),
                      ),
                      child: _typingDots(),
                    ),
                  );
                }
                return _bubble(_messages[i]);
              },
            ),
          ),
          const Divider(height: 1),
          Container(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 16),
            decoration: const BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Color(0x10211A4F),
                  blurRadius: 16,
                  offset: Offset(0, -4),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      hintText: 'Digite sua pergunta…',
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                FilledButton.icon(
                  onPressed: (_loading || typing) ? null : _send,
                  icon: const Icon(Icons.send_rounded, size: 18),
                  label: Text((_loading || typing) ? 'Gerando' : 'Enviar'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
