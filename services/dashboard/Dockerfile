FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY app ./app

CMD ["uv", "run", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
