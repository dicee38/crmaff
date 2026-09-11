#!/bin/sh
# Прод-энтрипоинт: прогоняет миграции перед стартом (безопасно при повторных
# деплоях - alembic upgrade head идемпотентен), затем запускает uvicorn.
# $PORT - обязателен на Render (платформа сама решает, какой порт слушать).
set -eu

echo "[entrypoint] alembic upgrade head..."
alembic upgrade head

if [ "$#" -gt 0 ]; then
  # docker-compose (dev) передаёт свою команду (напр. --reload) - уважаем её.
  echo "[entrypoint] starting: $*"
  exec "$@"
fi

echo "[entrypoint] starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-access-log
