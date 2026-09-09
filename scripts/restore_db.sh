#!/bin/sh
# Восстановление Postgres из бэкапа, созданного backup_db.sh.
#
# ВНИМАНИЕ: разворачивает дамп в указанную БД. По умолчанию это НЕ
# POSTGRES_DB (прод), а RESTORE_TARGET_DB - явно передайте
# POSTGRES_DB=<та же база>, если действительно хотите восстановить поверх
# продакшн-базы (осознанное разрушительное действие, не default).
#
# Использование: scripts/restore_db.sh <path-to-backup.sql.gz>

set -eu

BACKUP_FILE="${1:?Использование: restore_db.sh <path-to-backup.sql.gz>}"

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-crm}"
RESTORE_TARGET_DB="${RESTORE_TARGET_DB:-crm_restore_test}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "[restore] Файл не найден: $BACKUP_FILE" >&2
  exit 1
fi

echo "[restore] Пересоздаю базу $RESTORE_TARGET_DB на $POSTGRES_HOST:$POSTGRES_PORT"
PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS \"$RESTORE_TARGET_DB\";" \
  -c "CREATE DATABASE \"$RESTORE_TARGET_DB\";"

echo "[restore] Разворачиваю $BACKUP_FILE -> $RESTORE_TARGET_DB"
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
  -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$RESTORE_TARGET_DB" \
  -v ON_ERROR_STOP=1 -q

echo "[restore] Готово. Проверка:"
PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" \
  -d "$RESTORE_TARGET_DB" -c "\dt" -c "SELECT count(*) AS leads_count FROM leads;"
