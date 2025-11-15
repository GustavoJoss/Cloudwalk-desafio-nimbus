# app/deps.py
import os, json, pathlib, faiss, numpy as np, yaml
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from openai import OpenAI
from dotenv import load_dotenv, dotenv_values
from .seed_dataset import SEED_DOCS

BASE = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent          # raiz do projeto (onde ficam scrape.py e build_index.py)
ENV_PATH = PROJECT_ROOT / ".env"

IDX_PATH = PROJECT_ROOT / "index/faiss/index.faiss"
CHUNKS_TEXTS_PATH = PROJECT_ROOT / "data/chunks/texts.jsonl"
CHUNKS_META_PATH = PROJECT_ROOT / "data/chunks/meta.jsonl"

CHUNKS_TEXTS_PATH.parent.mkdir(parents=True, exist_ok=True)
IDX_PATH.parent.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_PATH)
env_file = {}
try:
    env_file = dotenv_values(ENV_PATH)
except Exception:
    env_file = {}

def _get_env(name: str, default: str | None = None):
    v = os.getenv(name)
    if not v:
        v = env_file.get(name, default)
    if not v and ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith(name + "="):
                v = line.split("=", 1)[1].strip()
                break
    return v

OPENAI_API_KEY = _get_env("OPENAI_API_KEY")
OPENAI_BASE_URL = _get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = _get_env("OPENAI_MODEL", "gpt-3.5-turbo")
EMBED_MODEL  = _get_env("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

print(f"[ENV] .env path={ENV_PATH} exists={ENV_PATH.exists()} has_key={'yes' if bool(OPENAI_API_KEY) else 'no'}")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não encontrada. Verifique o arquivo .env na raiz.")

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SCRAPE_SCRIPT = SCRIPTS_DIR / "scrape.py"
BUILD_INDEX_SCRIPT = SCRIPTS_DIR / "build_index.py"


def ensure_full_index_built():
    """
    Garante que o índice 'grande' (com scraping) exista.
    - Se index.faiss + texts/meta.jsonl já existem: não faz nada.
    - Se não existem:
        * Se scrape.py e build_index.py existirem -> executa os dois.
        * Se der erro, segue com índice mínimo de SEED_DOCS no __init__ do Store.
    Você pode controlar com BUILD_INDEX_ON_START:
        - BUILD_INDEX_ON_START=0  -> não roda scripts, usa só SEED_DOCS.
        - Se não definir ou for diferente de 0 -> tenta rodar scripts.
    """
    if IDX_PATH.exists() and CHUNKS_TEXTS_PATH.exists() and CHUNKS_META_PATH.exists():
        print("[INIT] Índice completo já existe em disco; não vou rodar scrape/build_index.")
        return

    flag = os.getenv("BUILD_INDEX_ON_START", "1").strip()
    if flag == "0":
        print("[INIT] BUILD_INDEX_ON_START=0 -> não vou rodar scrape/build_index. Usando apenas SEED_DOCS.")
        return

    if not SCRAPE_SCRIPT.exists() or not BUILD_INDEX_SCRIPT.exists():
        print("[INIT] scrape.py ou build_index.py não encontrados em", PROJECT_ROOT)
        print("[INIT] Vou seguir com índice mínimo de SEED_DOCS.")
        return

    import subprocess, sys

    try:
        print(f"[INIT] Executando scrape.py em {PROJECT_ROOT}...")
        subprocess.run(
            [sys.executable, str(SCRAPE_SCRIPT)],
            cwd=PROJECT_ROOT,
            check=True,
        )
        print(f"[INIT] Executando build_index.py em {PROJECT_ROOT}...")
        subprocess.run(
            [sys.executable, str(BUILD_INDEX_SCRIPT)],
            cwd=PROJECT_ROOT,
            check=True,
        )
        print("[INIT] scrape.py e build_index.py concluídos com sucesso.")
    except Exception as e:
        print(f"[INIT] Erro ao rodar scrape/build_index: {type(e).__name__}: {e}")
        print("[INIT] Vou seguir com índice mínimo baseado apenas em SEED_DOCS.")


class Store:
    def __init__(self):
        # Embedder (usado tanto para índice de disco quanto para SEED_DOCS extras)
        self.embedder = SentenceTransformer(EMBED_MODEL)

        # 0) tenta construir o índice completo (scraping) se ainda não existir
        ensure_full_index_built()

        # 1) Primeiro tenta carregar um índice existente (scrape + build_index)
        if IDX_PATH.exists() and CHUNKS_TEXTS_PATH.exists() and CHUNKS_META_PATH.exists():
            print("[INIT] Carregando índice existente de disco (scrape/build_index)...")
            self.index = faiss.read_index(str(IDX_PATH))
            self.texts = [
                json.loads(l)["text"]
                for l in open(CHUNKS_TEXTS_PATH, encoding="utf-8")
            ]
            self.meta = [
                json.loads(l)["url"]
                for l in open(CHUNKS_META_PATH, encoding="utf-8")
            ]
        else:
            # 2) Se não existir índice, cria um índice mínimo só com SEED_DOCS
            print("[INIT] Nenhum índice encontrado. Construindo índice mínimo com SEED_DOCS...")
            self.texts = [doc["text"] for doc in SEED_DOCS]
            self.meta = [doc["url"] for doc in SEED_DOCS]

            embs = self.embedder.encode(
                self.texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ).astype(np.float32)

            self.index = faiss.IndexFlatIP(embs.shape[1])
            self.index.add(embs)

            # salva esse índice mínimo para próximas execuções
            faiss.write_index(self.index, str(IDX_PATH))
            CHUNKS_TEXTS_PATH.write_text(
                "\n".join(json.dumps({"text": t}) for t in self.texts),
                encoding="utf-8",
            )
            CHUNKS_META_PATH.write_text(
                "\n".join(json.dumps({"url": u}) for u in self.meta),
                encoding="utf-8",
            )
            print("[INIT] Índice mínimo criado e salvo.")

        # 3) Agora, independente da origem, garantimos que os SEED_DOCS também estão presentes
        existing_urls = {str(u) for u in self.meta}
        extra_texts = []
        extra_meta = []

        for doc in SEED_DOCS:
            if doc["url"] not in existing_urls:
                extra_texts.append(doc["text"])
                extra_meta.append(doc["url"])

        if extra_texts:
            print(f"[INIT] Injetando {len(extra_texts)} SEED_DOCS extras no índice...")
            extra_embs = self.embedder.encode(
                extra_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ).astype(np.float32)

            self.index.add(extra_embs)
            self.texts.extend(extra_texts)
            self.meta.extend(extra_meta)

        # 4) BM25 em cima de TODOS os textos (scrape + seed)
        self.bm25 = BM25Okapi([t.split() for t in self.texts])

        # 5) Prompts
        with open(BASE/"prompts.yaml", encoding="utf-8") as f:
            p = yaml.safe_load(f)
        self.system = p["system"]
        self.styles = p["styles"]

        # 6) Cliente OpenAI
        self.llm = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def embed(self, q: str):
        return (
            self.embedder
            .encode([q], convert_to_numpy=True, normalize_embeddings=True)
            .astype(np.float32)
        )

STORE = None
def get_store():
    global STORE
    if STORE is None:
        STORE = Store()
    return STORE
