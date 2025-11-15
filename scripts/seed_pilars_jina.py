# scripts/seed_pilares_jina.py
import requests
from app.deps import get_store

URLS = [
    "https://r.jina.ai/https://www.cloudwalk.io/#our-pillars",
    "https://r.jina.ai/https://www.cloudwalk.io/code-of-ethics-and-conduct",
]

def add_to_store(text, url):
    s = get_store()
    s.texts.append(text)
    s.meta.append(url)
    emb = s.embed(text)
    s.index.add(emb)
    print("ADICIONADO:", url)

def main():
    s = get_store()
    existing = {str(m) for m in s.meta}

    for url in URLS:
        if url not in existing:
            print(">> Baixando", url)
            txt = requests.get(url).text
            add_to_store(txt, url)
        else:
            print(">> Já existe no índice:", url)

if __name__ == "__main__":
    main()
