# app/api/health.py
from fastapi import APIRouter

router = APIRouter(tags=["meta"])

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/version")
def version():
    return {"app": "cloudwalk-chatbot", "rev": "v1"}
