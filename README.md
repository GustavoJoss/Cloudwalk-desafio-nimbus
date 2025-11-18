## CloudWalk Chatbot – RAG + Flutter Front-end

**Chatbot capaz de explicar o que é a CloudWalk, seus produtos (como InfinitePay), missão, valores e Código de Ética.**

**As respostas incluem fontes reais citadas no formato [n].**

**Este projeto contém:**

- Back-end em FastAPI + RAG (scraping automático, BM25, FAISS, embeddings e LLM)

- Front-end em Flutter (web/mobile/desktop), com:

- markdown rendering

- efeito de digitação

- chips de fontes

- tema visual inspirado na InfinitePay

---

## Sumário

- [CloudWalk Chatbot – RAG + Flutter Front-end](#cloudwalk-chatbot--rag--flutter-front-end)
- [Sumário](#sumário)
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Configuração do Back-end (FastAPI/RAG)](#configuração-do-back-end-fastapirag)
- [Scraping \& Indexação](#scraping--indexação)
- [Rodando a API](#rodando-a-api)
- [Endpoints](#endpoints)
- [Front-end (Flutter)](#front-end-flutter)
- [CORS](#cors)
- [Exemplos de uso](#exemplos-de-uso)
  - [Exemplo 1 – O que é a CloudWalk e qual a relação com a InfinitePay?](#exemplo-1--o-que-é-a-cloudwalk-e-qual-a-relação-com-a-infinitepay)
  - [Exemplo 2 – Qual é a missão e quais são os valores da CloudWalk?](#exemplo-2--qual-é-a-missão-e-quais-são-os-valores-da-cloudwalk)
  - [Exemplo 3 – Código de Ética / uso da marca](#exemplo-3--código-de-ética--uso-da-marca)
- [Troubleshooting](#troubleshooting)
- [Decisoes tecnicas](#decisoes-tecnicas)

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

_Python 3.10+_

_Flutter SDK (3.22+ recomendado)_

_Navegador moderno (Chrome/Edge) para Flutter web_

_OpenAI API key ou Ollama rodando localmente (para LLM)_

---

## Configuração do Back-end (FastAPI/RAG)

- Na raiz do projeto:

  python -m venv .venv

- Windows

  .\.venv\Scripts\activate

- Linux/Mac

  source .venv/bin/activate

  pip install -r requirements.txt

  .env (OpenAI ou Ollama)

- Crie um arquivo .env na raiz (pode usar .env.example como base):

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

## Scraping & Indexação

**A indexação pode ser:**

- ✔️ Automática (padrão)

Ao subir a API, deps.py:

- verifica se existe índice FAISS

- caso não exista, executa:

- scripts/scrape.py

- scripts/build_index.py

- Controlado por:

- BUILD_INDEX_ON_START=1

- ✔️ Manual (debug)

  python scripts/scrape.py
  python scripts/build_index.py

---

## Rodando a API

**Na raiz:**

    uvicorn app.main:app --reload

- Swagger: http://127.0.0.1:8000/docs

- Health: http://127.0.0.1:8000/health

- Version: http://127.0.0.1:8000/version

## Endpoints

**POST /chat**

    Request (JSON):

    {
    "question": "O que é a CloudWalk e qual a relação com a InfinitePay?",
    "style": "default"
    }

_Resposta (exemplo):_

    A CloudWalk é uma empresa brasileira de tecnologia financeira [...].

    Fontes: [1] https://www.cloudwalk.io/#our-mission [2] https://www.infinitepay.io/pt-br/

- Todas as respostas citam as fontes como [n] url.

- GET /health

  { "ok": true }

- GET /version

  { "app": "cloudwalk-chatbot", "rev": "v1" }

---

## Front-end (Flutter)

**Configurar URL da API**

_Edite cloudwalk_chat/lib/api/chat_api.dart:_

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

_Em produção, use o domínio real, por exemplo:_

    defaultValue: 'https://api.seu-dominio.com',

**Rodar**

- No diretório cloudwalk_chat/:

  flutter pub get

_Rodar em desenvolvimento:_

- Web (Chrome/Edge):

  flutter run -d edge

**ou**

    flutter run -d chrome

**se der problema, use:**

    flutter run -d web-server

- Desktop (Windows):

  flutter run -d windows

_Lembre de subir o FastAPI antes, ou apontar o front para uma API já hospedada._

- Build de produção (web)
- flutter build web --release

  Saída: cloudwalk_chat/build/web/

- Você pode:

- servir esse build via Nginx/Apache; ou

- montar um StaticFiles no FastAPI apontando para o build/web.

- Feature set do front

- Renderização em Markdown (títulos, listas, código, links).

- Chips de fontes: host + contador “+N”.

- Efeito de digitação com timeout de segurança (evita loop infinito).

- Botão “Copiar” por resposta.

- Tema visual inspirado na InfinitePay (cores/tipografia em theme.dart).

- Indicador “digitando…” enquanto o LLM responde.

---

## CORS

- No app/main.py o CORS já está configurado para dev:

  allow_origins = ["*"]

- Em produção, prefira restringir:

  allow_origins = [
  "https://seu-dominio.com",
  "https://www.seu-dominio.com",
  ]

- Se outra pessoa (host diferente) for testar a API, adicione o domínio dela à lista.

  Proxy (Windows/PowerShell)

-- Se você configurou um proxy inválido e o Python/Flutter não consegue acessar a internet, pode limpar as variáveis de ambiente:

    $env:HTTP_PROXY=""
    $env:HTTPS_PROXY=""
    $env:ALL_PROXY=""
    $env:http_proxy=""
    $env:https_proxy=""
    $env:all_proxy=""
    $env:NO_PROXY="127.0.0.1,localhost,.local"

- Para proxies persistentes (HKCU\Environment), verifique as chaves de registro ou siga a documentação da sua empresa/Rede.

---

## Exemplos de uso

### Exemplo 1 – O que é a CloudWalk e qual a relação com a InfinitePay?

**Pergunta sugerida**

> O que é a CloudWalk e qual é a relação dela com a InfinitePay?

**Comportamento esperado do chatbot**

- Explicar que a **CloudWalk** é uma empresa brasileira de tecnologia financeira, sediada em **São Paulo**,  
  com a missão de criar a melhor rede de pagamentos do planeta.
- Destacar que a empresa busca **democratizar a indústria financeira** e empoderar empreendedores
  por meio de soluções tecnológicas inclusivas e transformadoras.
- Deixar claro que a **InfinitePay** é a marca de soluções de pagamento da CloudWalk,
  voltada para **pequenos e médios empreendedores** no Brasil.
- Explicar que, quando um lojista usa maquininhas ou links de pagamento da InfinitePay,
  ele está utilizando a **tecnologia e infraestrutura** desenvolvidas pela CloudWalk.
- Citar as fontes usadas nos contextos, por exemplo:
  - [1] Seção _Our Mission_ da CloudWalk
  - [2] Seção de _Facts_ sobre a empresa
  - [3] Site institucional da InfinitePay

---

### Exemplo 2 – Qual é a missão e quais são os valores da CloudWalk?

**Pergunta sugerida**

> Qual é a missão da CloudWalk e quais são os seus valores/pilares?

**Comportamento esperado do chatbot**

- Descrever a **missão** da CloudWalk como:
  - criar a melhor rede de pagamentos do planeta – e depois de outros planetas –,
  - democratizando a indústria financeira,
  - empoderando empreendedores por meio de soluções tecnológicas inclusivas e transformadoras.
- Explicar os **pilares/valores** da empresa, usando a nomenclatura original:
  - **Best Product** – foco em construir o melhor produto possível em tecnologia, performance e experiência;
  - **Customer Engagement** – clientes no centro das decisões, relacionamento de longo prazo e escuta ativa de feedback;
  - **Disruptive Economics** – modelo econômico que reduz custos para lojistas e torna os pagamentos mais justos e acessíveis.
- Deixar claro que o chatbot está **resumindo** os trechos dos contextos, sem inventar novos valores.
- Citar as fontes usadas nos contextos, por exemplo:
  - [1] Seção _Our Mission_ da CloudWalk
  - [2] Seção _Our Pillars_ / valores da CloudWalk

### Exemplo 3 – Código de Ética / uso da marca

**Pergunta sugerida**

> Quais são as regras para usar a marca da CloudWalk em eventos, entrevistas e materiais de comunicação?

**Comportamento esperado do chatbot**

    - Recuperar trechos do **Código de Ética e Conduta da CloudWalk**, em especial a parte de comunicação externa e uso da marca.
    - Explicar que:
    - colaboradores, parceiros, fornecedores e prestadores de serviço podem representar a marca,
        desde que alinhem previamente com a liderança e o time responsável pela marca;
    - o uso do logotipo, identidade visual e demais ativos de marca deve seguir os padrões definidos pela empresa.
    - Organizar a resposta em **tópicos**, deixando claro que está resumindo as orientações presentes nos contextos.
    - Não inventar nomes de pessoas nem regras adicionais que não estejam nos textos.
    - Se em alguma situação não houver informação suficiente nos contextos sobre um detalhe específico,
        o chatbot deve avisar que aquele ponto não aparece nos trechos recuperados, em vez de chutar.

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

---

## Decisoes tecnicas

**Por que RAG?**

- Permite respostas sempre fundamentadas em fontes reais

- Evita alucinação

- Permite atualização independente do modelo

- Por que FastAPI?

- framework leve, rápido e moderno

- validação automática

- documentação integrada

- ideal para microserviços/IA

**Por que Flutter?**

- entrega um front único para web, desktop e mobile

- ótima performance

- fácil integração com API REST

**Query Augmentation — Como funciona e por que não é estática agora**

_A query augmentation foi refeita para ser:_

- modular (regras em um dict/JSON)

- dinâmica (só adiciona termos relevantes)

- baseada em contexto (intenção → expansões diferentes)

Inicialmente, a query augmentation era feita de forma mais estática, com blocos fixos de texto para cada tipo de pergunta (missão, valores, ética, uso da marca etc.).

Refatorei essa parte para um modelo **dinâmico e configurável**, baseado em um arquivo JSON (`app/config/augmentation_rules.json`), onde:

- Cada _gatilho_ (por exemplo: `missao`, `valores`, `ética`, `marca`, `infinitepay`) é mapeado para uma lista de termos relacionados que aparecem nos textos oficiais (site, missão, pilares, código de ética, ajuda da InfinitePay, etc.).
- Quando o usuário faz uma pergunta, a função `get_expansions()` percorre os gatilhos e adiciona apenas as expansões relevantes para aquela query.
- A função `build_retrieval_query()` monta a query final combinando a pergunta original com os termos relacionados:

```python
    def build_retrieval_query(user_query: str) -> str:
        expansions = get_expansions(user_query)
        if not expansions:
            return user_query
        expansion_text = " ".join(expansions)
        return f"{user_query}\n\nTermos relacionados: {expansion_text}"
```
