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
