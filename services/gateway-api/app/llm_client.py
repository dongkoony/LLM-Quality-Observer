import time
import os
from litellm import completion

from .config import get_settings


def _configure_provider_env() -> None:
    settings = get_settings()

    if settings.llm_api_key:
        os.environ["OPENAI_API_KEY"] = settings.llm_api_key

    if settings.llm_api_base_url:
        os.environ["OPENAI_API_BASE"] = settings.llm_api_base_url


def _resolve_model(model_version: str | None) -> str:
    """
    요청에서 온 model_version이 이상하면 무시하고
    기본 모델(openai_model_main)을 쓰도록 정리.
    """
    settings = get_settings()

    if not model_version:
        return settings.openai_model_main

    # Swagger 기본 예제가 "string"이라서, 그 값이 오면 무시
    if model_version == "string":
        return settings.openai_model_main

    return model_version


def call_llm(prompt: str, model_version: str | None = None) -> dict:
    """
    LLM 호출 및 토큰 정보 추출 (v0.7.0 Phase 4 - LiteLLM 사용)

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
    settings = get_settings()
    _configure_provider_env()

    model = _resolve_model(model_version)
    models_to_try = list(dict.fromkeys([model, *settings.fallback_models]))

    last_error = None

    for attempt_model in models_to_try:
        try:
            start = time.perf_counter()

            # LiteLLM completion 호출
            response = completion(
                model=attempt_model,
                messages=[{"role": "user", "content": prompt}],
                timeout=settings.llm_timeout_seconds,
            )

            elapsed_ms = (time.perf_counter() - start) * 1000.0

            # 응답 텍스트 추출
            text = response.choices[0].message.content

            # 토큰 사용량 추출
            usage_obj = response.usage
            usage = {
                "input_tokens": getattr(usage_obj, "prompt_tokens", 0),
                "output_tokens": getattr(usage_obj, "completion_tokens", 0),
                "total_tokens": getattr(usage_obj, "total_tokens", 0),
                "cached_tokens": getattr(usage_obj, "cache_read_input_tokens", 0),
                "reasoning_tokens": getattr(usage_obj, "reasoning_tokens", 0),
            }

            return {
                "response": text,
                "model_version": attempt_model,
                "latency_ms": elapsed_ms,
                "usage": usage,
            }

        except Exception as e:
            print(f"[LiteLLM] Model {attempt_model} failed: {e}")
            last_error = e
            continue

    # 모든 모델 실패 시
    raise Exception(f"All models failed. Last error: {last_error}")
