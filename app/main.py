# app/main.py
import os
for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
    os.environ.pop(k, None)
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost,.local")

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .deps import get_store
from .api import chat, health  # importa routers

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

@app.on_event("startup")
def warm():
    get_store()

# registra as rotas
app.include_router(chat.router)
app.include_router(health.router)
