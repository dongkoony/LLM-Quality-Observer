from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import LLMLog
from .schemas import ChatRequest, ChatResponse
from .llm_client import call_llm
from .config import settings

# 최초 실행 시 테이블 생성 (간단 버전)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM Quality Observer - Gateway API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


def resolve_model_version(request_model: str | None) -> str:
    """
    요청에서 들어온 model_version이 없거나 Swagger 기본값("string")이면
    환경변수로 설정한 기본 모델(openai_model_main)을 사용한다.
    """
    if not request_model or request_model == "string":
        return settings.openai_model_main
    return request_model


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 실제로 사용할 모델 이름 계산
    used_model = resolve_model_version(request.model_version)

    # LLM 호출 (사용할 모델 명을 넘겨줌)
    response_text, latency_ms = call_llm(request.prompt, used_model)

    # DB 로그 저장
    log = LLMLog(
        user_id=request.user_id,
        prompt=request.prompt,
        response=response_text,
        model_version=used_model,
        latency_ms=latency_ms,
        status="success",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # 클라이언트 응답
    return ChatResponse(
        response=response_text,
        model_version=used_model,
        latency_ms=latency_ms,
    )
