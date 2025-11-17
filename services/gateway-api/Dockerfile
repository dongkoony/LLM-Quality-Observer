FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 시스템 의존성 (psycopg2용)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --upgrade pip && pip install uv

# pyproject만 먼저 복사 후 의존성 설치
COPY pyproject.toml ./
RUN uv sync --no-dev

# 실제 애플리케이션 코드 복사
COPY app ./app

# FastAPI 실행
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
