import os
for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
    os.environ.pop(k, None)
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost,.local")
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .rag import generate_answer
from .deps import get_store

app = FastAPI(title="CloudWalk Chatbot")

ENV = os.getenv("ENV", "dev")

if ENV == "dev":
    allow_origins = ["*"]  
else:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,          
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type", "Authorization", "Accept", "Origin",
        "X-Requested-With", "X-Api-Key"
    ],
    expose_headers=["Content-Type"], 
    max_age=86400,                   
)


class ChatIn(BaseModel):
    question: str
    style: str | None = "default"

class ChatOut(BaseModel):
    answer: str

@app.on_event("startup")
def warm():
    get_store()

@app.post("/chat", response_model=ChatOut)
def chat(p: ChatIn):
    try:
        return ChatOut(answer=generate_answer(p.question, style=p.style or "default"))
    except Exception as e:
        logging.exception("Erro no /chat")
        
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"app": "cloudwalk-chatbot", "rev": "v1"}
