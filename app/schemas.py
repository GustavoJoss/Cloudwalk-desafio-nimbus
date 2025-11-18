from pydantic import BaseModel

class ChatIn(BaseModel):
    question: str
    style: str | None = "default"

class ChatOut(BaseModel):
    answer: str
