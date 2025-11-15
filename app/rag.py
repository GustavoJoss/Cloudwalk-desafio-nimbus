# app/rag.py
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import logging
from .deps import get_store

# limite (segundos) de quanto vamos esperar pela resposta do LLM
LLM_TIMEOUT_SECS = 90
LLM_MAX_TOKENS = 600

def build_retrieval_query(user_query: str) -> str:
    """
    Reescreve a query do usuário para aproximar de palavras-chave
    que existem nos textos (missão, valores, história, código de ética, uso da marca etc.).
    """
    q = user_query.lower()

    # se for claramente financeiro, não mexe
    termos_financeiros = [
        "preço", "preco", "taxa", "tarifa", "cobrança",
        "cobranca", "faturamento", "receita", "valuation"
    ]
    if any(t in q for t in termos_financeiros):
        return user_query

    # valores/pilares -> reforça pilares e cultura
    if "valor" in q or "pilar" in q:
        return (
            "valores da CloudWalk enquanto cultura, pilares, princípios, filosofia, "
            "our pillars, Best Product, Customer Engagement, Disruptive Economics, "
            "código de ética, princípios culturais da CloudWalk"
        )

    # missão -> reforça our mission
    if "missao" in q or "missão" in q or "mission" in q:
        return (
            "missão da CloudWalk criar a melhor rede de pagamentos na Terra e em outros planetas "
            "democratizar a indústria financeira empoderar empreendedores soluções tecnológicas "
            "inclusivas e transformadoras our mission"
        )
    
    # história / fundador
    if "historia" in q or "história" in q or "fundador" in q or "fundada" in q:
        return (
            "história da CloudWalk fundador Luis Silva sede São Paulo fatos essenciais "
            "fundação objetivo transformar a indústria de pagamentos relação com InfinitePay"
        )

    # código de ética / conduta
    if "etica" in q or "ética" in q or "conduta" in q or "codigo de etica" in q:
        return (
            "código de ética e conduta da CloudWalk conflitos de interesse uso da marca "
            "lavagem de dinheiro financiamento ao terrorismo ambiente de trabalho "
            "integridade transparência compliance"
        )

    # uso da marca / representantes / regras da marca
    if (
        "uso da marca" in q
        or "usar a marca" in q
        or "usar a marca da cloudwalk" in q
        or "representar a marca" in q
        or "representar a cloudwalk" in q
        or "representantes usar a marca" in q
        or ("marca" in q and "cloudwalk" in q and ("regras" in q or "diretrizes" in q))
    ):
        return (
            "código de ética e conduta da CloudWalk uso da marca e comunicação externa "
            "quem representa a CloudWalk em eventos entrevistas podcasts ou painéis "
            "uso do logotipo identidade visual e demais ativos de marca "
            "alinhamento prévio com liderança e time responsável pela marca "
            "diretrizes para representantes e uso da marca da CloudWalk"
        )

    return user_query



def retrieve(query: str, k=6):
    s = get_store()

    # reescreve a query para casos como "valores da cloudwalk"
    retr_query = build_retrieval_query(query)

    # busca vetorial
    D, I = s.index.search(s.embed(retr_query), k)
    hits = [(s.texts[i], s.meta[i]) for i in I[0]]

    # mistura BM25 para diversidade (usando a query reescrita também)
    bm = s.bm25.get_top_n(retr_query.split(), list(range(len(s.texts))), n=k)
    for i in bm:
        par = (s.texts[i], s.meta[i])
        if par not in hits:
            hits.append(par)

    # se a pergunta fala de CloudWalk, prioriza URLs da CloudWalk,
    # especialmente our-pillars e code-of-ethics
    q_lower = query.lower()
    precisa_etica_marca = (
        "uso da marca" in q_lower
        or "usar a marca" in q_lower
        or "marca da cloudwalk" in q_lower
        or "representantes usar a marca" in q_lower
        or ("marca" in q_lower and "cloudwalk" in q_lower and ("regras" in q_lower or "diretrizes" in q_lower))
    )

    if precisa_etica_marca and not any(
        "code-of-ethics-and-conduct" in str(u) for _, u in hits
    ):
        # procura um chunk cujo URL seja o código de ética e injeta no topo dos hits
        for text, url in zip(s.texts, s.meta):
            if "code-of-ethics-and-conduct" in str(url):
                hits.insert(0, (text, url))
                break

    return hits[:k]

def format_ctx(hits):
    ctx = []
    refs = []
    for j, (t, url) in enumerate(hits, 1):
        ctx.append(f"[{j}] Fonte: {url}\nTrecho: {t[:1200]}")
        refs.append((j, url))
    return "\n\n".join(ctx), refs

def generate_answer(query: str, style="default"):
    s = get_store()
    q_lower = query.lower()

    termos_sensiveis = [
        "faturamento", "receita", "receita anual", "lucro", "prejuízo", "prejuizo",
        "valuation", "avaliacao", "avaliação", "preço de mercado", "preco de mercado",
        "quantos clientes", "quantidade de clientes", "número de clientes",
        "volume transacionado", "volume processado", "gmv", "market cap",
        "quantas transações", "quantas vendas", "metrics", "indicadores"
    ]

    # Para perguntas financeiras, sempre responde "não sei" se não houver contexto explícito
    if any(t in q_lower for t in termos_sensiveis):
        return (
            "Não encontrei informações suficientes nos contextos para responder com precisão. "
            "Este assistente nunca apresenta números, estimativas, métricas financeiras ou "
            "quantidade de clientes sem evidência direta nos trechos recuperados."
        )
    
    # Recupera contextos e monta prompt
    ctx, refs = format_ctx(retrieve(query))
    extra_req = (
        "Regras IMPORTANTES para a resposta:\n"
        "- Use SOMENTE os trechos presentes em CONTEXTOS.\n"
        "- Nunca invente dados, fatos, números, métricas ou quantidades.\n"
        "- Se a pergunta envolver clientes, faturamento, receita, volume transacionado "
        "ou qualquer dado financeiro e isso não estiver claramente nos CONTEXTOS, "
        "diga explicitamente que não há informação suficiente nos contextos para responder.\n"
        "- Não introduza nomes de pessoas ou cargos que não apareçam nos CONTEXTOS. "
        "Se precisar citar alguém, use apenas nomes explicitamente presentes nos trechos.\n"
        "- Se não houver nenhuma informação nos CONTEXTOS sobre o tema da pergunta, "
        "explique claramente que não encontrou resposta nos trechos.\n"
        "- Se houver qualquer informação relacionada nos CONTEXTOS, responda usando esses trechos, "
        "mesmo que a informação seja parcial ou resumida, deixando claro quando a resposta for limitada.\n"
    )

    # País / sede
    if any(t in q_lower for t in ["país", "pais", "sede", "onde fica", "de qual país"]):
        extra_req += (
            "\n- Se os CONTEXTOS trouxerem o país de origem e a cidade da sede da CloudWalk, "
            "mencione os dois explicitamente (por exemplo: 'empresa brasileira, sediada em São Paulo, Brasil')."
        )

    # Representar / uso da marca
    if any(t in q_lower for t in [
        "representa", "representar", "representante", "representantes",
        "eventos", "entrevista", "podcast", "painel", "uso da marca", "usar a marca"
    ]):
        extra_req += (
            "\n- Sobre quem pode representar a CloudWalk ou usar a marca em eventos, entrevistas, podcasts "
            "ou painéis, não invente regras nem cite pessoas específicas (como fundador ou CEO) "
            "a menos que isso esteja literalmente escrito nos CONTEXTOS.\n"
            "- Se os CONTEXTOS mencionarem grupos como colaboradores, parceiros, fornecedores "
            "ou prestadores de serviço, explique que são esses grupos que podem representar a "
            "empresa, desde que sigam as diretrizes de alinhamento com liderança e time de marca.\n"
            "- Se houver trechos falando de 'uso da marca' ou 'comunicação externa', transforme essas orientações "
            "em tópicos claros para o usuário, em vez de dizer que não há informações."
        )

    # Perguntas que falam explicitamente de regras / diretrizes
    if any(t in q_lower for t in ["regras", "regra", "diretrizes", "diretriz", "política", "politica"]):
        extra_req += (
            "\n- Como a pergunta menciona 'regras', 'diretrizes' ou 'política', organize a resposta em tópicos, "
            "resumindo como regras ou diretrizes aquilo que estiver descrito nos CONTEXTOS.\n"
            "- Não invente regras novas: apenas reformule em bullet points o que já aparece nos trechos.\n"
            "- Se existir ao menos uma orientação relacionada ao tema nos CONTEXTOS, você DEVE apresentá-la; "
            "não responda que 'não há informações suficientes' se houver alguma orientação explícita."
        )

    prompt = f"""{s.styles.get(style, s.styles['default'])}

    {extra_req}

CONTEXTOS:
{ctx}

Pergunta: {query}
- Use apenas os CONTEXTOS. Cite as fontes como [n].
- Se alguma parte da resposta não estiver clara ou explícita nos CONTEXTOS, diga claramente que essa parte não aparece nos trechos.
- Se houver qualquer informação relacionada nos CONTEXTOS, use esses trechos para montar a resposta, mesmo que de forma parcial, deixando claro quando algo for limitado.
"""

    # função que chama o cliente do LLM sem timeout (parâmetros permitidos)
    def _call_llm():
        # NÃO usar request_timeout aqui (causa TypeError em alguns SDKs)
        return s.llm.chat.completions.create(
            model=s.model,
            messages=[
                {"role": "system", "content": s.system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=LLM_MAX_TOKENS,
        )

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_call_llm)
            r = fut.result(timeout=LLM_TIMEOUT_SECS)

        # extrai o texto (compatível com retorno do SDK estilo OpenAI-like)
        answer = r.choices[0].message.content
        return answer + "\n\n" + "Fontes: " + " ".join(f"[{i}] {u}" for i, u in refs)

    except FutureTimeout:
        logging.warning("LLM timeout after %s seconds", LLM_TIMEOUT_SECS)
        fallback = "Erro: tempo limite ao gerar resposta. Tente novamente ou peça uma resposta mais concisa."
        if ctx:
            # mostra uma prévia dos trechos recuperados para o usuário
            fallback += "\n\nTrechos recuperados (prévia):\n" + (ctx[:1500] + ("..." if len(ctx) > 1500 else ""))
        return fallback

    except Exception as e:
        logging.exception("Erro ao chamar LLM")
        return f"Erro ao gerar resposta: {type(e).__name__}: {e}"
