"""
Prometheus 메트릭 정의 및 수집.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time

# 애플리케이션 정보
app_info = Info('llm_gateway_app', 'LLM Gateway API application info')
app_info.info({'version': '0.5.0', 'service': 'gateway-api'})

# HTTP 요청 관련 메트릭
http_requests_total = Counter(
    'llm_gateway_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'llm_gateway_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# LLM 호출 관련 메트릭
llm_requests_total = Counter(
    'llm_gateway_llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

llm_request_duration_seconds = Histogram(
    'llm_gateway_llm_request_duration_seconds',
    'LLM request latency in seconds',
    ['model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

llm_tokens_total = Counter(
    'llm_gateway_llm_tokens_total',
    'Total tokens processed',
    ['model', 'type']  # type: prompt, completion
)

# 데이터베이스 관련 메트릭
db_queries_total = Counter(
    'llm_gateway_db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'llm_gateway_db_query_duration_seconds',
    'Database query latency',
    ['operation', 'table']
)

# 로그 저장 메트릭
logs_saved_total = Counter(
    'llm_gateway_logs_saved_total',
    'Total logs saved to database',
    ['status']
)

# 현재 상태 게이지
active_requests = Gauge(
    'llm_gateway_active_requests',
    'Number of active HTTP requests'
)


class MetricsMiddleware:
    """
    FastAPI 미들웨어로 HTTP 요청 메트릭을 자동 수집.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        method = scope['method']
        path = scope['path']

        # /metrics 엔드포인트는 제외
        if path == '/metrics':
            await self.app(scope, receive, send)
            return

        active_requests.inc()
        start_time = time.time()

        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                duration = time.time() - start_time

                # 메트릭 기록
                http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=status_code
                ).inc()

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            active_requests.dec()


def record_llm_request(model: str, status: str, duration_seconds: float, tokens: dict = None):
    """
    LLM 요청 메트릭 기록.

    Args:
        model: 모델 이름
        status: 'success' or 'error'
        duration_seconds: 요청 소요 시간 (초)
        tokens: {'prompt': int, 'completion': int}
    """
    llm_requests_total.labels(model=model, status=status).inc()
    llm_request_duration_seconds.labels(model=model).observe(duration_seconds)

    if tokens:
        if 'prompt' in tokens:
            llm_tokens_total.labels(model=model, type='prompt').inc(tokens['prompt'])
        if 'completion' in tokens:
            llm_tokens_total.labels(model=model, type='completion').inc(tokens['completion'])


def record_db_query(operation: str, table: str, duration_seconds: float):
    """
    데이터베이스 쿼리 메트릭 기록.

    Args:
        operation: 'insert', 'select', 'update', 'delete'
        table: 테이블 이름
        duration_seconds: 쿼리 소요 시간 (초)
    """
    db_queries_total.labels(operation=operation, table=table).inc()
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration_seconds)


def record_log_saved(status: str):
    """
    로그 저장 메트릭 기록.

    Args:
        status: 'success' or 'error'
    """
    logs_saved_total.labels(status=status).inc()
