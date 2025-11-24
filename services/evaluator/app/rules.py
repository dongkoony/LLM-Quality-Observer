from .models import LLMLog
from .schemas import EvaluationResult


def basic_rule_evaluate(log: LLMLog) -> EvaluationResult:
    """
    간단한 룰 기반 평가 함수.
    OpenAI API를 호출하지 않고, 순수 룰만으로 LLM 응답을 평가함.

    평가 기준:
    1. 응답 길이가 너무 짧으면 점수 낮춤
    2. 에러 관련 키워드가 포함되면 플래그 처리
    3. 그 외에는 정상으로 판단

    Args:
        log: 평가할 LLMLog 인스턴스

    Returns:
        EvaluationResult: 평가 결과 (점수, 라벨, 코멘트 등)
    """
    response_text = log.response or ""
    response_length = len(response_text)

    # 기본값 설정
    overall_score = 5
    is_flagged = False
    label = "ok"
    comment = "Looks fine by basic rules."

    # 룰 1: 응답 길이 체크
    if response_length < 30:
        overall_score = 2
        label = "too_short"
        comment = f"Response is too short (length: {response_length} chars)."

    # 룰 2: 에러 관련 키워드 감지
    error_keywords = ["error", "exception", "traceback", "failed", "stack overflow"]
    response_lower = response_text.lower()

    detected_keywords = [kw for kw in error_keywords if kw in response_lower]

    if detected_keywords:
        overall_score = 1
        is_flagged = True
        label = "error_like"
        comment = f"Response looks like an error message. Detected keywords: {', '.join(detected_keywords)}"

    # 평가 결과 반환
    return EvaluationResult(
        log_id=log.id,
        overall_score=overall_score,
        is_flagged=is_flagged,
        label=label,
        judge_model="rule-basic-v1",
        comment=comment,
    )
