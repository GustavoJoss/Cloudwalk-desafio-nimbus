# CloudWalk Chatbot (RAG) + Flutter Front-end

Chatbot que explica o que é a CloudWalk, seus produtos (ex.: InfinitePay), missão, valores e código de ética,
sempre citando as fontes usadas na resposta.

- Back-end em **FastAPI** com **RAG** (scraping de páginas públicas + FAISS + BM25 + LLM OpenAI/Ollama).
- Front-end em **Flutter** (web/mobile/desktop), com:
  - renderização em Markdown;
  - links clicáveis;
  - chips com fontes;
  - efeito de digitação com timeout de segurança.

---

## Sumário

- [Sumário](#sumário)
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Configuração do Back-end (FastAPI/RAG)](#configuração-do-back-end-fastapirag)
- [Índice (scraping) – automático vs manual](#índice-scraping--automático-vs-manual)
- [Subir API (dev)](#subir-api-dev)
- [Endpoints](#endpoints)
- [Front-end (Flutter)](#front-end-flutter)
- [Instalar dependências \& rodar](#instalar-dependências--rodar)
- [CORS](#cors)
- [Para atualizar o sumário:](#para-atualizar-o-sumário)
- [Exemplos de uso](#exemplos-de-uso)
- [Troubleshooting](#troubleshooting)

---

## Arquitetura

```text
cloudwalk-chatbot/
├─ app/                     # FastAPI
│  ├─ main.py               # API (/chat, /health, /version)
│  ├─ rag.py                # Recuperação + prompt + chamada LLM
│  ├─ deps.py               # Carrega FAISS/BM25/embeddings/LLM/prompts + auto build do índice
│  ├─ prompts.yaml          # System prompt + estilos de resposta
│  └─ seed_dataset.py       # SEED_DOCS (missão, pilares, ética, fatos essenciais)
├─ scripts/
│  ├─ scrape.py             # Coleta HTML e salva em data/raw/*.txt
│  └─ build_index.py        # Chunking + embeddings (all-MiniLM-L6-v2) + FAISS
├─ data/
│  ├─ raw/                  # Textos brutos do scrape
│  └─ chunks/               # Chunks + metadados (jsonl)
├─ index/
│  └─ faiss/                # Índice FAISS
├─ cloudwalk_chat/          # Flutter app (front-end)
│  ├─ lib/
│  │  ├─ api/chat_api.dart  # Cliente HTTP -> FastAPI
│  │  ├─ models/message.dart
│  │  ├─ pages/chat_page.dart
│  │  ├─ theme.dart         # Paleta InfinitePay (cores/tipografia)
│  │  └─ main.dart          # App root
│  └─ pubspec.yaml
├─ .env                     # Config do LLM (OpenAI/Ollama) + ajustes
└─ requirements.txt

```

---

## Requisitos

    Python 3.10+

    Flutter SDK (3.22+ recomendado)

    Navegador moderno (Chrome/Edge) para Flutter web

    OpenAI API key ou Ollama rodando localmente (para LLM)

---

## Configuração do Back-end (FastAPI/RAG)

    Na raiz do projeto:

    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    # source .venv/bin/activate

    pip install -r requirements.txt

    .env (OpenAI ou Ollama)

    Crie um arquivo .env na raiz (pode usar .env.example como base):

    Opção A)

    Ollama (local, sem custo por chamada)
    OPENAI_API_KEY=ollama
    OPENAI_BASE_URL=http://127.0.0.1:11434/v1
    OPENAI_MODEL=llama3.2          # ex.: llama3.2, llama3.2:3b-instruct, qwen2.5:3b-instruct
    EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2


    Dica: baixe o modelo uma vez antes:

    ollama run llama3.2 "oi"

    Opção B)

    OpenAI (nuvem)
    OPENAI_API_KEY=SEU_TOKEN
    OPENAI_BASE_URL=https://api.openai.com/v1
    OPENAI_MODEL=gpt-4o-mini
    EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

---

## Índice (scraping) – automático vs manual

    O back-end usa um índice (FAISS + BM25) com:

    páginas raspadas (CloudWalk, InfinitePay, ajuda InfinitePay etc.);

    textos essenciais embutidos no código (SEED_DOCS).

    Modo automático (recomendado)

    Na primeira vez que a API sobe, o Store em app/deps.py:

    Verifica se o índice existe em index/faiss/index.faiss e data/chunks/*.jsonl.

    Se não existir, executa automaticamente:

    scripts/scrape.py

    scripts/build_index.py

    Carrega o índice em memória e injeta os SEED_DOCS.

    Esse comportamento pode ser controlado pela variável:

    # 1 (padrão) = tenta rodar scripts automaticamente
    # 0          = não roda scripts; usa apenas índice mínimo com SEED_DOCS
    BUILD_INDEX_ON_START=1

    Modo manual (útil para debug ou rebuild)

    Se preferir rodar manualmente, na raiz do projeto:

    # coleta
    python scripts/scrape.py

    # indexação (embeddings + FAISS + BM25)
    python scripts/build_index.py


    Se quiser começar “do zero”, apague:

    index/faiss/

    data/chunks/

    e depois deixe o modo automático reconstruir tudo na próxima subida.

---

## Subir API (dev)

    Na raiz:

    uvicorn app.main:app --reload


    Swagger: http://127.0.0.1:8000/docs

    Health: http://127.0.0.1:8000/health

    Version: http://127.0.0.1:8000/version

## Endpoints

    POST /chat

    Request (JSON):

    {
    "question": "O que é a CloudWalk e qual a relação com a InfinitePay?",
    "style": "default"
    }


    Response (exemplo):

    A CloudWalk é uma empresa brasileira de tecnologia financeira [...].

    Fontes: [1] https://www.cloudwalk.io/#our-mission [2] https://www.infinitepay.io/pt-br/


    Todas as respostas citam as fontes como [n] url.

    GET /health

    { "ok": true }


    GET /version

    { "app": "cloudwalk-chatbot", "rev": "v1" }

---

## Front-end (Flutter)

    Configurar URL da API

    Edite cloudwalk_chat/lib/api/chat_api.dart:

    class ChatApi {
        static const String _base = String.fromEnvironment(
            'API_BASE',
            defaultValue: 'http://127.0.0.1:8000', // altere para a URL da API em produção
        );

        Future<String> ask(String q, {String style = 'default'}) async {
            final url = Uri.parse('$_base/chat');
            // ...
        }
    }


    Em produção, use o domínio real, por exemplo:

    defaultValue: 'https://api.seu-dominio.com',

## Instalar dependências & rodar

    No diretório cloudwalk_chat/:

    flutter pub get


    Rodar em desenvolvimento:

    Web (Chrome/Edge):

    flutter run -d edge
    # ou
    flutter run -d chrome
    # se der problema, use:
    flutter run -d web-server


    Desktop (Windows):

    flutter run -d windows


    Lembre de subir o FastAPI antes, ou apontar o front para uma API já hospedada.

    Build de produção (web)
    flutter build web --release


    Saída: cloudwalk_chat/build/web/

    Você pode:

    servir esse build via Nginx/Apache; ou

    montar um StaticFiles no FastAPI apontando para o build/web.

    Feature set do front

    Renderização em Markdown (títulos, listas, código, links).

    Chips de fontes: host + contador “+N”.

    Efeito de digitação com timeout de segurança (evita loop infinito).

    Botão “Copiar” por resposta.

    Tema visual inspirado na InfinitePay (cores/tipografia em theme.dart).

    Indicador “digitando…” enquanto o LLM responde.

## CORS

    No app/main.py o CORS já está configurado para dev:

    allow_origins = ["*"]


    Em produção, prefira restringir:

    allow_origins = [
        "https://seu-dominio.com",
        "https://www.seu-dominio.com",
    ]


    Se outra pessoa (host diferente) for testar a API, adicione o domínio dela à lista.

    Proxy (Windows/PowerShell)

    Se você configurou um proxy inválido e o Python/Flutter não consegue acessar a internet, pode limpar as variáveis de ambiente:

    $env:HTTP_PROXY=""
    $env:HTTPS_PROXY=""
    $env:ALL_PROXY=""
    $env:http_proxy=""
    $env:https_proxy=""
    $env:all_proxy=""
    $env:NO_PROXY="127.0.0.1,localhost,.local"


    Para proxies persistentes (HKCU\Environment), verifique as chaves de registro ou siga a documentação da sua empresa/Rede.

    Formatação & TOC no VS Code

    Extensões úteis:

    Prettier – Code Formatter (esbenp.prettier-vscode)

    Markdown All in One (yzhang.markdown-all-in-one)

    Exemplo de settings.json:

    {
    "editor.formatOnSave": true,
    "[markdown]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.wordWrap": "on",
        "editor.quickSuggestions": false
    },
    "prettier.proseWrap": "preserve",
    "prettier.printWidth": 100,
    "markdown.extension.toc.updateOnSave": true,
    "markdown.extension.toc.levels": "2..6",
    "markdown.extension.toc.slugifyMode": "github",
    "markdown.extension.tableFormatter.enabled": true
    }

---

## Para atualizar o sumário:

    Ctrl+Shift+P → Markdown All in One: Create/Update Table of Contents.

---

## Exemplos de uso

    Exemplo 1 – O que é a CloudWalk e a relação com a InfinitePay?

    A CloudWalk é uma empresa brasileira de tecnologia financeira, sediada em São Paulo, que tem como missão
    criar a melhor rede de pagamentos do planeta. A InfinitePay é a marca de soluções de pagamento da
    CloudWalk voltada para pequenos e médios empreendedores no Brasil [...]

    Fontes:
    [1] https://www.cloudwalk.io/#our-mission

    [2] https://www.cloudwalk.io/#facts

    [3] https://www.infinitepay.io/pt-br/

    Exemplo 2 – Missão e valores

    A missão da CloudWalk é criar a melhor rede de pagamentos do planeta – e depois de outros planetas –
    democratizando a indústria financeira e empoderando empreendedores por meio de soluções tecnológicas
    inclusivas e transformadoras. Seus pilares são Best Product, Customer Engagement e Disruptive Economics [...]

    Fontes:
    [1] https://www.cloudwalk.io/#our-mission

    [2] https://www.cloudwalk.io/#our-pillars

    Exemplo 3 – Código de Ética / uso da marca

    Quem representa a CloudWalk em eventos, entrevistas, podcasts ou painéis deve alinhar previamente com a
    liderança e com o time responsável pela marca, seguindo as diretrizes de uso do logotipo, identidade
    visual e demais ativos de marca [...]

    Fontes:
    [1] https://www.cloudwalk.io/code-of-ethics-and-conduct

    As respostas variam conforme as páginas coletadas e o modelo configurado (OpenAI/Ollama).

---

## Troubleshooting

    - Chrome/Edge não abre com Flutter web

        Use flutter run -d web-server ou atualize o navegador.

    - Ollama não responde

        Verifique se o serviço está rodando:

        ollama --version

        ollama run llama3.2 "oi"

        Confirme se a porta 11434 está livre.

    - Erro de proxy / timeout em downloads de modelos

        Verifique se há proxy corporativo.

        Se estiver usando proxy, garanta que 127.0.0.1 e localhost estejam em NO_PROXY.

    - CORS bloqueando requisições

        Confirme que o domínio do front está presente em allow_origins no CORSMiddleware.

        Em desenvolvimento, ["*"] costuma ser suficiente.

```

```
