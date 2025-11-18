# app/rag.py
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import logging
from .deps import get_store
import json
from pathlib import Path
from typing import List, Dict

RULES_PATH = Path(__file__).parent / "config" / "augmentation_rules.json"
try:
    with RULES_PATH.open(encoding="utf-8") as f:
        AUG_RULES: Dict[str, List[str]]
except Exception:
    AUG_RULES = {}  # fallback seguro

# limite (segundos) de quanto vamos esperar pela resposta do LLM
LLM_TIMEOUT_SECS = 90
LLM_MAX_TOKENS = 600

def get_expansions(user_query: str) -> list[str]:
    """
    Gera expansões dinâmicas baseadas na presença de palavras-chave.
    Se a pergunta contiver termos definidos em AUG_RULES,
    adiciona termos relacionados para melhorar a recuperação vetorial/BM25.
    """
    q = user_query.lower()
    expansions = []

    for trigger, terms in AUG_RULES.items():
        if trigger in q:
            expansions.extend(terms)

    # remove duplicados preservando ordem
    seen = set()
    unique = []
    for t in expansions:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique

def build_retrieval_query(user_query: str) -> str:
    """
    Reescreve a query de forma dinâmica e escalável.
    - Mantém a pergunta original.
    - Adiciona expansões relevantes.
    - Não engessa a query com blocos fixos.
    """
    expansions = get_expansions(user_query)

    if not expansions:
        # sem expansões → usa só o texto original
        return user_query
    
    # junta tudo em um texto mais rico
    expansion_text = " ".join(expansions)
    return f"{user_query}\n\nTermos relacionados: {expansion_text}"



def retrieve(query: str, k=6):
    s = get_store()
    q_lower = query.lower()

    # 0) Perguntas claramente sobre uso da marca / representantes
    precisa_etica_marca = (
        "uso da marca" in q_lower
        or "usar a marca" in q_lower
        or "marca da cloudwalk" in q_lower
        or "representantes usar a marca" in q_lower
        or ("marca" in q_lower and "cloudwalk" in q_lower and ("regras" in q_lower or "diretrizes" in q_lower))
    )

    if precisa_etica_marca:
        # pega TODOS os chunks cujo URL é o código de ética e conduta
        etica_hits = [
            (text, url)
            for text, url in zip(s.texts, s.meta)
            if "code-of-ethics-and-conduct" in str(url)
        ]
        if etica_hits:
            # devolve só esses (até k)
            return etica_hits[:k]
        # se por algum motivo não achar, cai pro fluxo padrão abaixo

    # 1) Fluxo padrão: reescreve query e faz busca vetorial + BM25
    retr_query = build_retrieval_query(query)

    D, I = s.index.search(s.embed(retr_query), k)
    hits = [(s.texts[i], s.meta[i]) for i in I[0]]

    bm = s.bm25.get_top_n(retr_query.split(), list(range(len(s.texts))), n=k)
    for i in bm:
        par = (s.texts[i], s.meta[i])
        if par not in hits:
            hits.append(par)

    # 2) Se falar de CloudWalk, dá um boost pra URLs da CloudWalk
    if "cloudwalk" in q_lower:
        def sort_key(hit):
            text, url = hit
            u = str(url)
            score = 0
            if "cloudwalk.io" in u:
                score -= 1
            if ("missao" in q_lower or "missão" in q_lower) and "our-mission" in u:
                score -= 3
            if ("valor" in q_lower or "pilar" in q_lower) and (
                "our-pillars" in u or "code-of-ethics" in u
            ):
                score -= 2
            return score

        hits.sort(key=sort_key)

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
