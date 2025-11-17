from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    user_id: str | None = None
    model_version: str | None = None


class ChatResponse(BaseModel):
    response: str
    model_version: str | None = None
    latency_ms: float | None = None


class LLMLogRead(BaseModel):
    id: int
    created_at: datetime
    user_id: str | None
    prompt: str
    response: str
    model_version: str | None
    latency_ms: float | None
    status: str

    class Config:
        from_attributes = True
