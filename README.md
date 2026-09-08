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
