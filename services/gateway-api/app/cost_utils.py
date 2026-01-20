"""
Cost calculation utilities for LLM usage (v0.7.0)
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from .models import LLMModelPricing


def get_model_pricing(db: Session, model_name: str) -> Optional[LLMModelPricing]:
    """
    데이터베이스에서 모델 가격 정보 조회

    Args:
        db: Database session
        model_name: Model name (e.g., "gpt-5-mini")

    Returns:
        LLMModelPricing object or None if not found
    """
    return db.query(LLMModelPricing).filter(
        LLMModelPricing.model_name == model_name,
        LLMModelPricing.is_active == True
    ).first()


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int,
    pricing: LLMModelPricing
) -> tuple[Decimal, Decimal, Decimal]:
    """
    토큰 사용량 기반 비용 계산

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cached_tokens: Number of cached tokens (subset of input_tokens)
        pricing: Model pricing information

    Returns:
        Tuple of (cost_input, cost_output, cost_total) in USD
    """
    # 캐시되지 않은 입력 토큰
    uncached_input_tokens = input_tokens - cached_tokens

    # 입력 비용 계산 (uncached + cached)
    cost_input = Decimal(
        (uncached_input_tokens * float(pricing.price_input_per_1m) / 1_000_000) +
        (cached_tokens * float(pricing.price_cached_per_1m or 0) / 1_000_000)
    )

    # 출력 비용 계산
    cost_output = Decimal(
        output_tokens * float(pricing.price_output_per_1m) / 1_000_000
    )

    # 총 비용
    cost_total = cost_input + cost_output

    return (
        cost_input.quantize(Decimal('0.000001')),
        cost_output.quantize(Decimal('0.000001')),
        cost_total.quantize(Decimal('0.000001'))
    )


def get_default_pricing_fallback(model_name: str) -> dict:
    """
    데이터베이스에 가격 정보가 없을 때 사용할 기본 가격

    Args:
        model_name: Model name

    Returns:
        Dictionary with pricing info
    """
    # GPT-5 mini를 기본값으로 사용 (가장 일반적)
    return {
        "price_input_per_1m": Decimal("0.25"),
        "price_output_per_1m": Decimal("2.00"),
        "price_cached_per_1m": Decimal("0"),
    }
