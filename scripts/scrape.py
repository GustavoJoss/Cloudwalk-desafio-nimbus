import pathlib, re, time, hashlib, os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------- CONFIG ----------
START_URLS = [
    "https://www.cloudwalk.io/",
    "https://www.cloudwalk.io/press",
    "https://www.cloudwalk.io/#our-mission",
    "https://blog.cloudwalk.io/",
    "https://www.infinitepay.io/pt-br/",
    "https://www.infinitepay.io/newsroom/",
    "https://ajuda.infinitepay.io/hc/pt-br",
    "https://www.cloudwalk.io/sitemap.xml",
    "https://www.cloudwalk.io/careers",
    "https://blog.cloudwalk.io/",
    "https://www.infinitepay.io/pt-br/",
    "https://www.infinitepay.io/newsroom/",
    "https://www.infinitepay.io/sobre-nos",
    "https://ajuda.infinitepay.io/hc/pt-br",
    "https://r.jina.ai/https://www.cloudwalk.io/#our-mission",
    "https://www.cloudwalk.io/code-of-ethics-and-conduct",
    "https://www.cloudwalk.io/#our-pillars",
    "https://r.jina.ai/https://www.cloudwalk.io/#our-pillars",
    "https://www.linkedin.com/company/cloudwalk/about/",
    "https://textise.net/showtext.aspx?strURL=https://www.cloudwalk.io/#our-pillars",
    "https://www.cloudwalk.io/newsroom/luis-silva-cloudwalk-ceo-named-one-of-bloomberg-lineas-100-most-innovative-people-in-latin-america-in-2024/",
    "https://www.infinitepay.io/newsroom/luis-silva-fundador-da-cloudwalk-e-destaque-em-ranking-dos-mais-influentes-da-bloomberg-lineas/",
    "https://ajuda.infinitepay.io/pt-BR/articles/7913300-como-comecar-a-vender-com-a-infinitepay",

]
MAX_PAGES = 200
MAX_WORKERS = 16
MAX_IN_FLIGHT = 48
PER_HOST_LIMIT = 8
CONNECT_TIMEOUT = 4
READ_TIMEOUT = 8
SLEEP_BETWEEN = 0.15
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.3",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}
ALLOWED_HOSTS = {urlparse(u).netloc for u in START_URLS}
OUT = pathlib.Path("data/raw"); OUT.mkdir(parents=True, exist_ok=True)


session = requests.Session()
retry = Retry(
    total=3, connect=3, read=3, backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "HEAD"]
)
session.mount("http://", HTTPAdapter(max_retries=retry))
session.mount("https://", HTTPAdapter(max_retries=retry))


def _clean(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script","style","noscript"]): t.extract()
    for sel in ["header","nav","footer",".cookie",".cookies",".newsletter"]:
        [x.extract() for x in soup.select(sel)]
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s{2,}", " ", text)
    return text

def _ok(url:str)->bool:
    net = urlparse(url).netloc
    if net not in ALLOWED_HOSTS: return False
    if any(url.lower().endswith(ext) for ext in (".pdf",".jpg",".jpeg",".png",".svg",".gif",".zip",".mp4",".webm",".ico")):
        return False
    return True

def _save(url, text):
    h = hashlib.md5(url.encode()).hexdigest()
    (OUT / f"{h}.txt").write_text(url + "\n\n" + text, encoding="utf-8")

def _fetch_raw(url: str) -> tuple[int, str, str]:
    """Retorna (status, content_type, text) sem renderização JS."""
    r = session.get(url, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    return r.status_code, r.headers.get("Content-Type",""), r.text

def _fetch_with_fallback(url: str) -> str | None:
    netloc = urlparse(url).netloc

    # 1) Para CloudWalk, força Jina (melhor texto para RAG)
    if "cloudwalk.io" in netloc:
        try:
            prox = f"https://r.jina.ai/{url}"
            r = session.get(prox, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            if r.status_code == 200:
                txt = _clean(r.text)
                if len(txt) >= 200:
                    return txt
        except Exception:
            pass
        return None  # se der ruim, deixa sem texto mesmo

    # 2) Para outros domínios, mantém lógica antiga (HTML normal + fallback)
    try:
        status, ctype, html = _fetch_raw(url)
        if status == 200 and "text/html" in ctype:
            txt = _clean(html)
            if len(txt) >= 300:
                return txt
    except Exception:
        pass

    try:
        prox = f"https://r.jina.ai/{url}"
        r = session.get(prox, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        if r.status_code == 200:
            txt = _clean(r.text)
            if len(txt) >= 200:
                return txt
    except Exception:
        pass

    return None

def crawl():
    if not START_URLS:
        print("Adicione START_URLS no arquivo!"); return
    seen=set(); q=list(START_URLS); n=0
    while q and n < MAX_PAGES:
        url=q.pop(0)
        base = url.split("#",1)[0]  
        if base in seen or not _ok(base): continue
        seen.add(base)
        try:
            text = _fetch_with_fallback(url)
            if text:
                _save(base, text); n+=1
                status, ctype, html = _fetch_raw(base)
                if status==200 and "text/html" in ctype:
                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all("a", href=True):
                        nxt = urljoin(base, a["href"])
                        if _ok(nxt) and nxt.split("#",1)[0] not in seen:
                            q.append(nxt)
            time.sleep(SLEEP_BETWEEN)
        except Exception:
            pass
    print(f"Coletadas {n} páginas.")

if __name__=="__main__":
    crawl()
