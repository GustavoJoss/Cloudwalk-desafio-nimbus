# scripts/add_cloudwalk_core_docs.py

import pathlib
import hashlib
import requests
from bs4 import BeautifulSoup
import re

OUT = pathlib.Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

DOCS = [
    # HOME: missão + pilares (HTML direto)
    {
        "url": "https://www.cloudwalk.io/",
        "fetch": "https://www.cloudwalk.io/",
        "mode": "html",
        "required": True,
    },
    # MISSÃO (via Jina – reforça a parte da missão)
    {
        "url": "https://www.cloudwalk.io/#our-mission",
        "fetch": "https://r.jina.ai/https://www.cloudwalk.io/#our-mission",
        "mode": "text",
        "required": False,
    },
    # CÓDIGO DE ÉTICA (valores/princípios gerais)
    {
        "url": "https://www.cloudwalk.io/code-of-ethics-and-conduct",
        "fetch": "https://r.jina.ai/https://www.cloudwalk.io/code-of-ethics-and-conduct",
        "mode": "text",
        "required": True,
    },
]


def clean_html(html: str) -> str:
    """Remove scripts/estilos e extrai texto da página da CloudWalk."""
    soup = BeautifulSoup(html, "html.parser")

    # tira coisas muito gerais
    for t in soup(["script", "style", "noscript"]):
        t.extract()
    for sel in ["header", "nav", "footer", ".cookie", ".cookies", ".newsletter"]:
        for x in soup.select(sel):
            x.extract()

    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s{2,}", " ", text)
    return text


def save_doc(url, text):
    h = hashlib.md5(url.encode()).hexdigest()
    fp = OUT / f"{h}.txt"
    fp.write_text(url + "\n\n" + text, encoding="utf-8")
    print("SALVO:", fp, "->", url)


def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=25)
    print("STATUS", r.status_code, "para", url)
    r.raise_for_status()
    return r.text


def main():
    for doc in DOCS:
        print("Baixando:", doc["fetch"])
        try:
            raw = fetch(doc["fetch"])
            if doc["mode"] == "html":
                text = clean_html(raw)
            else:
                text = raw  # Jina já devolve texto/markdown
            save_doc(doc["url"], text)
        except requests.HTTPError as e:
            if doc.get("required", False):
                raise
            else:
                print(f"AVISO: falhou para {doc['fetch']} ({e}), "
                      "mas não é obrigatório. Continuando...")


if __name__ == "__main__":
    main()
