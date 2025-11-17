from dataclasses import dataclass


@dataclass
class EvalConfig:
    min_length: int = 10
    max_length: int = 2000
    forbidden_terms: tuple[str, ...] = (
        "forbidden_example",
        "badword",
    )


def compute_rule_score(response: str, config: EvalConfig | None = None) -> float:
    """
    아주 단순한 룰 기반 스코어:
    - 길이 체크
    - 금지어 포함 여부
    """
    if config is None:
        config = EvalConfig()

    text = response or ""
    length = len(text)

    if length == 0:
        return 0.0

    score = 1.0

    # 길이 너무 짧거나 긴 경우 페널티
    if length < config.min_length:
        score -= 0.4
    if length > config.max_length:
        score -= 0.2

    # 금지어 포함 시 페널티
    lowered = text.lower()
    for term in config.forbidden_terms:
        if term.lower() in lowered:
            score -= 0.5
            break

    # 0 ~ 1로 클램프
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    return score


def label_from_score(score: float) -> str:
    """
    간단한 라벨링 규칙:
    - score >= 0.8  -> GOOD
    - 0.5 <= score < 0.8 -> WARN
    - score < 0.5 -> BAD
    """
    if score >= 0.8:
        return "GOOD"
    if score >= 0.5:
        return "WARN"
    return "BAD"
