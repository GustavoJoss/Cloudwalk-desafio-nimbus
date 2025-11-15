# scripts/debug.py

from app.deps import get_store
from app.rag import retrieve


def debug_core_docs():
    """
    Mostra os documentos principais da CloudWalk no índice:
    - missão (#our-mission)
    - pilares (#our-pillars)
    - código de ética (code-of-ethics-and-conduct)
    """
    s = get_store()
    targets = (
        "our-mission",
        "our-pillars",
        "code-of-ethics-and-conduct",
    )

    print("=== CORE DOCS (missão / pilares / ética) ===")
    found = False
    for idx, (txt, meta) in enumerate(zip(s.texts, s.meta)):
        url = str(meta)
        if any(t in url for t in targets):
            found = True
            print(">>> ENCONTREI CORE DOC")
            print("INDEX:", idx)
            print("URL:", url)
            print("TRECHO:", txt[:500].replace("\n", " "))
            print("-----")

    if not found:
        print("NENHUM core doc (missão/pilares/ética) encontrado no índice.")
    print()


def debug_search_terms():
    """
    Procura termos-chave dentro de QUALQUER chunk do índice.
    Útil pra ver se 'Customer Engagement', 'Disruptive Economics', etc. existem.
    """
    s = get_store()
    terms = ["Customer Engagement", "Disruptive Economics", "Best Product"]
    print("=== BUSCA POR TERMOS-CHAVE NO ÍNDICE ===")
    for term in terms:
        found = False
        for idx, (txt, meta) in enumerate(zip(s.texts, s.meta)):
            if term.lower() in txt.lower():
                if not found:
                    print(f">>> ENCONTREI '{term}' em:")
                found = True
                print("INDEX:", idx)
                print("URL:", meta)
                print("TRECHO:", txt[:300].replace("\n", " "))
                print("-----")
                break
        if not found:
            print(f"NÃO ENCONTREI o termo '{term}' em nenhum chunk.")
    print()


def debug_retrieve_examples():
    """
    Mostra o que o RAG está recuperando para perguntas típicas.
    """
    questions = [
        "qual é a missao da cloudwalk?",
        "quais sao os valores da cloudwalk?",
        "quais sao os pilares da cloudwalk?",
    ]

    for q in questions:
        print("=== RETRIEVE PARA:", q, "===")
        hits = retrieve(q, k=6)
        for j, (t, url) in enumerate(hits, 1):
            print(f"[{j}] URL:", url)
            print("TRECHO:", t[:400].replace("\n", " "))
            print("-----")
        print()


if __name__ == "__main__":
    debug_core_docs()
    debug_search_terms()
    debug_retrieve_examples()
