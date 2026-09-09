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

## Нагрузочное тестирование

NFR: P95 latency < 300ms для списка лидов и карточки лида (см. CLAUDE.md).

```bash
# 1. Засеять реалистичный объём данных (по умолчанию 20 000 лидов)
PYTHONPATH=. python scripts/seed_load_test_data.py --leads 20000

# 2. Погонять нагрузку на GET /leads и GET /leads/{id}/card
python scripts/run_load_test.py --base-url http://127.0.0.1:8000 --concurrency 30 --requests 40
```

Прогон на 20k лидов, concurrency=30 (1200 запросов): P95 ≈ 210ms (список), ≈ 250ms (карточка) — укладывается в бюджет. Все под-запросы карточки выполняются с использованием индексов (`ix_*_lead_id`) за <0.1ms на стороне Postgres (проверено `EXPLAIN ANALYZE`); наблюдавшаяся до фикса деградация (P95 > 450ms на concurrency=20-30) была вызвана слишком маленьким пулом соединений SQLAlchemy (дефолт 5+10) — см. `app/database.py` (`pool_size=40, max_overflow=40` для Postgres).

Синтетические данные не коммитятся и не остаются в БД — скрипт помечает их `loadtest-*` префиксами, чистить вручную (см. `DELETE ... WHERE external_click_id LIKE 'loadtest-click-%'` и аналогично для `tracking_events`/`affiliate_events`/`users`) после прогона.
