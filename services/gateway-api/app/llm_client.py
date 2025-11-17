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


def call_llm(prompt: str, model_version: str | None = None) -> tuple[str, float]:
    """
    GPT-5 mini를 기본으로 쓰는 LLM 호출 함수.
    model_version이 들어오면 그걸 우선 사용하되,
    이상한 값은 무시하고 기본 모델을 사용한다.
    """
    model = _resolve_model(model_version)

    start = time.perf_counter()

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    text = response.output_text

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return text, elapsed_ms
