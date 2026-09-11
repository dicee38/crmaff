FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

# --no-access-log: дефолтный access-log uvicorn пишет query-строку без
# редактирования (утечка секретов в query-параметрах вебхуков) - вместо
# него RequestLoggingMiddleware (app/middleware/request_logging.py).
# Энтрипоинт прогоняет alembic upgrade head перед стартом и слушает $PORT
# (обязательно для Render - платформа сама назначает порт).
ENTRYPOINT ["./docker-entrypoint.sh"]
