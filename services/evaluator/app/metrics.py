"""
Prometheus 메트릭 정의 및 수집 - Evaluator Service
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# 애플리케이션 정보
app_info = Info('llm_evaluator_app', 'LLM Evaluator Service application info')
app_info.info({'version': '0.5.0', 'service': 'evaluator'})

# 평가 관련 메트릭
evaluations_total = Counter(
    'llm_evaluator_evaluations_total',
    'Total evaluations performed',
    ['judge_type', 'status']  # judge_type: rule/llm, status: success/error
)

evaluation_duration_seconds = Histogram(
    'llm_evaluator_evaluation_duration_seconds',
    'Evaluation processing time',
    ['judge_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

evaluation_scores = Histogram(
    'llm_evaluator_evaluation_scores',
    'Distribution of evaluation scores',
    ['judge_type', 'score_type'],  # score_type: overall/instruction/truthfulness
    buckets=(1, 2, 3, 4, 5)
)

# 배치 평가 관련 메트릭
batch_evaluations_total = Counter(
    'llm_evaluator_batch_evaluations_total',
    'Total batch evaluation runs',
    ['judge_type']
)

batch_logs_processed = Histogram(
    'llm_evaluator_batch_logs_processed',
    'Number of logs processed per batch',
    buckets=(1, 5, 10, 20, 50, 100)
)

# 알림 관련 메트릭
notifications_sent_total = Counter(
    'llm_evaluator_notifications_sent_total',
    'Total notifications sent',
    ['channel', 'type', 'status']  # channel: slack/discord/email, type: alert/summary
)

low_quality_alerts_total = Counter(
    'llm_evaluator_low_quality_alerts_total',
    'Total low quality alerts triggered',
    ['judge_type']
)

# 스케줄러 관련 메트릭
scheduler_runs_total = Counter(
    'llm_evaluator_scheduler_runs_total',
    'Total scheduler runs',
    ['status']  # success/error
)

pending_logs_gauge = Gauge(
    'llm_evaluator_pending_logs',
    'Number of logs waiting for evaluation'
)

# LLM Judge 호출 메트릭
llm_judge_requests_total = Counter(
    'llm_evaluator_llm_judge_requests_total',
    'Total LLM judge API requests',
    ['model', 'status']
)

llm_judge_request_duration_seconds = Histogram(
    'llm_evaluator_llm_judge_request_duration_seconds',
    'LLM judge API request latency',
    ['model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf'))
)


def record_evaluation(judge_type: str, status: str, duration_seconds: float, scores: dict = None):
    """
    평가 메트릭 기록.

    Args:
        judge_type: 'rule' or 'llm'
        status: 'success' or 'error'
        duration_seconds: 평가 소요 시간 (초)
        scores: {'overall': int, 'instruction': int, 'truthfulness': int}
    """
    evaluations_total.labels(judge_type=judge_type, status=status).inc()
    evaluation_duration_seconds.labels(judge_type=judge_type).observe(duration_seconds)

    if scores and status == 'success':
        if 'overall' in scores:
            evaluation_scores.labels(
                judge_type=judge_type,
                score_type='overall'
            ).observe(scores['overall'])

        if 'instruction' in scores and scores['instruction'] is not None:
            evaluation_scores.labels(
                judge_type=judge_type,
                score_type='instruction'
            ).observe(scores['instruction'])

        if 'truthfulness' in scores and scores['truthfulness'] is not None:
            evaluation_scores.labels(
                judge_type=judge_type,
                score_type='truthfulness'
            ).observe(scores['truthfulness'])


def record_batch_evaluation(judge_type: str, logs_processed: int):
    """
    배치 평가 메트릭 기록.

    Args:
        judge_type: 'rule' or 'llm'
        logs_processed: 처리한 로그 개수
    """
    batch_evaluations_total.labels(judge_type=judge_type).inc()
    batch_logs_processed.observe(logs_processed)


def record_notification(channel: str, notification_type: str, status: str):
    """
    알림 전송 메트릭 기록.

    Args:
        channel: 'slack', 'discord', 'email'
        notification_type: 'alert' or 'summary'
        status: 'success' or 'error'
    """
    notifications_sent_total.labels(
        channel=channel,
        type=notification_type,
        status=status
    ).inc()


def record_low_quality_alert(judge_type: str):
    """
    낮은 품질 경고 메트릭 기록.

    Args:
        judge_type: 'rule' or 'llm'
    """
    low_quality_alerts_total.labels(judge_type=judge_type).inc()


def record_scheduler_run(status: str):
    """
    스케줄러 실행 메트릭 기록.

    Args:
        status: 'success' or 'error'
    """
    scheduler_runs_total.labels(status=status).inc()


def update_pending_logs_count(count: int):
    """
    대기 중인 로그 수 업데이트.

    Args:
        count: 현재 대기 중인 로그 개수
    """
    pending_logs_gauge.set(count)


def record_llm_judge_request(model: str, status: str, duration_seconds: float):
    """
    LLM Judge API 호출 메트릭 기록.

    Args:
        model: 모델 이름
        status: 'success' or 'error'
        duration_seconds: 요청 소요 시간 (초)
    """
    llm_judge_requests_total.labels(model=model, status=status).inc()
    llm_judge_request_duration_seconds.labels(model=model).observe(duration_seconds)
