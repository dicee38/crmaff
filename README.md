# Binolla Affiliate CRM

Контекст и архитектура проекта — см. [CLAUDE.md](./CLAUDE.md).

## Быстрый старт

```bash
cp .env.example .env

docker compose up -d postgres redis
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head
uvicorn app.main:app --reload
```

## Тесты

```bash
pytest -v
```

Тесты используют SQLite in-memory (см. `tests/conftest.py`) и не требуют поднятого Postgres.

## Frontend

```bash
cd frontend
cp .env.example .env   # VITE_API_BASE_URL по умолчанию указывает на localhost:8000

npm install
npm run dev             # http://localhost:5173
npm run build            # тайпчек + продакшн-сборка
```

Требует запущенный backend (см. выше) — `CORS_ORIGINS` в корневом `.env` должен включать origin фронтенда.

## Backups

Ежедневный бэкап Postgres — NFR, не опционально (см. CLAUDE.md).

```bash
# Разовый бэкап (локально, при поднятом docker compose up -d postgres)
POSTGRES_HOST=localhost sh scripts/backup_db.sh
# -> backups/crm_<timestamp>.sql.gz

# Проверка восстановления (разворачивает в отдельную БД crm_restore_test,
# продакшн-базу не трогает)
sh scripts/restore_db.sh backups/crm_<timestamp>.sql.gz
```

Автоматический ежедневный запуск:
- **Локально/self-hosted**: `docker compose --profile backup up -d backup` — поднимает сайдкар-контейнер, который дёргает `backup_db.sh` раз в сутки и складывает дампы в `./backups`.
- **Прод (Railway)**: Railway Cron Job, вызывающий тот же `scripts/backup_db.sh` с продовыми `POSTGRES_*` переменными окружения. Файлы бэкапа должны уезжать во внешнее хранилище (S3-совместимое и т.п.) — `BACKUP_DIR` можно примонтировать на volume с автосинком, конкретный provider выбирается на этапе деплоя.

Ротация: бэкапы старше `BACKUP_RETENTION_DAYS` (по умолчанию 14) удаляются автоматически при каждом запуске `backup_db.sh`.
