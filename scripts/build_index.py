import os, json, pathlib
from sentence_transformers import SentenceTransformer
import numpy as np, faiss

RAW = pathlib.Path("data/raw")
CHD = pathlib.Path("data/chunks"); CHD.mkdir(parents=True, exist_ok=True)
IDX = pathlib.Path("index/faiss"); IDX.mkdir(parents=True, exist_ok=True)
EMBED_MODEL = os.getenv("EMBED_MODEL","sentence-transformers/all-MiniLM-L6-v2")

def load_docs():
    docs=[]
    for fp in RAW.glob("*.txt"):
        url, body = fp.read_text(encoding="utf-8").split("\n\n",1)
        docs.append({"url":url, "text":body})
    return docs

def chunk(text, size=900, overlap=150):
    words=text.split(); i=0; out=[]
    while i < len(words):
        out.append(" ".join(words[i:i+size])); i += (size-overlap)
    return [t for t in out if len(t.split())>60]

def main():
    docs=load_docs()
    texts, meta=[], []
    for d in docs:
        for c in chunk(d["text"]):
            texts.append(c); meta.append(d["url"])
    model=SentenceTransformer(EMBED_MODEL)
    embs=model.encode(texts, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
    index=faiss.IndexFlatIP(embs.shape[1]); index.add(embs)
    faiss.write_index(index, str(IDX/"index.faiss"))
    (CHD/"texts.jsonl").write_text("\n".join(json.dumps({"text":t}) for t in texts), encoding="utf-8")
    (CHD/"meta.jsonl").write_text("\n".join(json.dumps({"url":u}) for u in meta), encoding="utf-8")
    print(f"Indexados {len(texts)} chunks.")
if __name__=="__main__":
    main()
