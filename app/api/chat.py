import logging
from fastapi import APIRouter, HTTPException
from ..schemas import ChatIn, ChatOut
from ..rag import generate_answer

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatOut)
def chat(p: ChatIn):
    try:
        answer = generate_answer(p.question, style=p.style or "default")
        return ChatOut(answer=answer)
    except Exception as e:
        logging.exception("Erro no /chat")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
