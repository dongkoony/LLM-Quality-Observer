import time

from openai import OpenAI

from .config import settings

# 전역 클라이언트 한 번만 생성
client = OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_api_base_url or None,
)


def _resolve_model(model_version: str | None) -> str:
    """
    요청에서 온 model_version이 이상하면 무시하고
    기본 모델(openai_model_main)을 쓰도록 정리.
    """
    if not model_version:
        return settings.openai_model_main

    # Swagger 기본 예제가 "string"이라서, 그 값이 오면 무시
    if model_version == "string":
        return settings.openai_model_main

    return model_version


def call_llm(prompt: str, model_version: str | None = None) -> dict:
    """
    LLM 호출 및 토큰 정보 추출 (v0.7.0)

    Returns:
        {
            "response": str,
            "model_version": str,
            "latency_ms": float,
            "usage": {
                "input_tokens": int,
                "output_tokens": int,
                "total_tokens": int,
                "cached_tokens": int,
                "reasoning_tokens": int
            }
        }
    """
    model = _resolve_model(model_version)

    start = time.perf_counter()

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    text = response.output_text
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    # Extract token usage (v0.7.0)
    usage = {
        "input_tokens": getattr(response.usage, "input_tokens", 0),
        "output_tokens": getattr(response.usage, "output_tokens", 0),
        "total_tokens": getattr(response.usage, "total_tokens", 0),
        "cached_tokens": getattr(response.usage, "cached_tokens", 0),
        "reasoning_tokens": getattr(response.usage, "reasoning_tokens", 0),
    }

    return {
        "response": text,
        "model_version": model,
        "latency_ms": elapsed_ms,
        "usage": usage,
    }
