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

# 의존성만 먼저 설치 (프로젝트 자체는 설치 안 함)
COPY pyproject.toml ./
RUN uv pip install --system \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    psycopg2-binary \
    pydantic \
    pydantic-settings

# 실제 애플리케이션 코드 복사
COPY *.py ./

# FastAPI 실행 (uv run 대신 직접 uvicorn 실행)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
