import json
import textwrap
import time
from typing import TypedDict

from fastapi import HTTPException
from openai import (
    OpenAI,
    RateLimitError,
    APIError,
    APIConnectionError,
    AuthenticationError,
)

from .config import settings
from .models import LLMLog


class EvaluationResult(TypedDict):
    score_overall: int
    score_instruction_following: int
    score_truthfulness: int
    comments: str
    raw_judge_response: str


client = OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_api_base_url or None,
)


def build_evaluation_prompt(log: LLMLog) -> str:
    """
    LLM-as-a-judge용 프롬프트.
    JSON만 반환하도록 강하게 요구한다.
    """
    prompt = f"""
    You are an expert evaluator for large language model outputs.

    You will be given:
    - A user prompt
    - The model's response

    Evaluate the response according to these criteria (1 to 5, integer only):
    - score_overall: Overall quality and usefulness.
    - score_instruction_following: How well the response follows the user's instructions.
    - score_truthfulness: How factually accurate and non-misleading the response is.

    Return ONLY a valid JSON object with the following structure:

    {{
      "score_overall": 1,
      "score_instruction_following": 1,
      "score_truthfulness": 1,
      "comments": "Short explanation in English."
    }}

    Do not include any additional text outside the JSON.

    --- USER PROMPT ---
    {log.prompt}

    --- MODEL RESPONSE ---
    {log.response}
    """

    # indentation 정리
    return textwrap.dedent(prompt).strip()


def _parse_eval_json(text: str) -> EvaluationResult:
    """
    Judge 모델의 텍스트 응답을 JSON으로 파싱.
    실패하면 HTTPException 던져서 상위에서 처리.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse judge JSON: {e}. Raw text: {text[:200]}",
        )

    def _get_int(key: str) -> int:
        value = data.get(key)
        if not isinstance(value, int):
            raise HTTPException(
                status_code=502,
                detail=f"Invalid type for {key}, expected int, got {type(value)}",
            )
        return value

    score_overall = _get_int("score_overall")
    score_instruction_following = _get_int("score_instruction_following")
    score_truthfulness = _get_int("score_truthfulness")

    comments = str(data.get("comments", ""))

    return EvaluationResult(
        score_overall=score_overall,
        score_instruction_following=score_instruction_following,
        score_truthfulness=score_truthfulness,
        comments=comments,
        raw_judge_response=text,
    )


def run_judge(log: LLMLog) -> EvaluationResult:
    """
    하나의 LLMLog에 대해 Judge LLM을 호출하고 EvaluationResult 반환.
    """
    prompt = build_evaluation_prompt(log)

    try:
        start = time.perf_counter()
        response = client.responses.create(
            model=settings.openai_model_judge,
            input=prompt,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM judge quota exceeded. Please check billing/usage.",
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key for judge model.",
        )
    except APIConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to judge model provider.",
        )
    except APIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM judge API error: {e}",
        )

    text = response.output_text
    eval_result = _parse_eval_json(text)

    # 원하면 elapsed_ms도 eval_result에 추가할 수 있음
    return eval_result
