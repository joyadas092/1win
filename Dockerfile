FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN useradd -m -u 1000 botuser

COPY --from=builder /install /usr/local
COPY main.py .
COPY bot/ ./bot/

RUN mkdir -p logs && chown -R botuser:botuser /app

USER botuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD python -c "from bot.config import settings; settings.validate()" || exit 1

CMD ["python", "main.py"]
