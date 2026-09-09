#!/bin/sh
# Ежедневный бэкап Postgres (NFR из CLAUDE.md: "Ежедневные автоматические
# backups PostgreSQL + периодическая проверка восстановления").
#
# Запускать по расписанию: Railway Cron Job (прод) либо host cron / compose
# сервис `backup` (локально) - см. README.md, раздел "Backups".
#
# Использует переменные окружения из .env (или уже экспортированные):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
#   BACKUP_DIR (по умолчанию ./backups)
#   BACKUP_RETENTION_DAYS (по умолчанию 14 - старые бэкапы старше N дней удаляются)

set -eu

BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-crm}"
POSTGRES_DB="${POSTGRES_DB:-crm}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="$BACKUP_DIR/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

echo "[backup] Дамп $POSTGRES_DB@$POSTGRES_HOST:$POSTGRES_PORT -> $OUT_FILE"

PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
  -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" \
  --format=plain --no-owner --no-privileges "$POSTGRES_DB" \
  | gzip > "$OUT_FILE"

echo "[backup] Готово: $(du -h "$OUT_FILE" | cut -f1)"

echo "[backup] Удаляю бэкапы старше $BACKUP_RETENTION_DAYS дн."
find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.sql.gz" -mtime "+${BACKUP_RETENTION_DAYS}" -print -delete
