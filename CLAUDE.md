# CLAUDE.md — CRM affiliate-платформы

Этот файл — контекст проекта для Claude Code. Читай его перед началом любой задачи в этом репозитории. Полное ТЗ (с обоснованиями и деталями) — `docs/tz-crm.docx` / см. историю чата; здесь — только то, что нужно держать в контексте при написании кода.

## Что это за проект

CRM-подсистема affiliate-платформы для арабоязычного трафика.
Вертикаль: Forex / бинарные опционы. Партнёр: **Binolla**.
Стартовые GEO: **Сирия (Levantine Arabic), Марокко (Moroccan Darija), Саудовская Аравия (Gulf/Najdi Arabic)**.
Коммуникация с лидами — через **Chatterfy** (Telegram CRM), поверх уже существующей webhook-интеграции на FastAPI/Railway.

Сквозная цепочка, которую должна поддерживать система:
`Click → Lead ID → Manager → Registration → Target Event (FTD) → Commission → Analytics`

## Стек

| Слой | Технология |
|---|---|
| Backend | Python, FastAPI (async) |
| БД | PostgreSQL 15+ |
| Кэш/очереди | Redis |
| Frontend | React + TypeScript |
| Хостинг | Railway (уже используется под Chatterfy-интеграцию) |
| Proxy/CDN | Cloudflare |
| Мониторинг ошибок | Sentry |
| Контейнеры | Docker |

## Команды

```bash
# заполнить реальными командами по мере настройки репозитория
docker compose up -d          # поднять Postgres + Redis локально
alembic upgrade head          # применить миграции
uvicorn app.main:app --reload # dev-сервер backend
pytest                        # тесты backend
npm run dev                   # dev-сервер frontend (в /frontend)
npm run test                  # тесты frontend
```

## Архитектура (поток данных)

```
Traffic (Telegram Ads / landing) → Tracking API → Lead ID
Lead ID → CRM (PostgreSQL) → Auto-assignment → Manager
Chatterfy (Telegram) ⇄ Webhook ⇄ CRM Communications
Binolla postback → Webhook → Event Engine → Lead ID → Revenue Attribution
CRM Data → Dashboard / Analytics API
```

На каждом уровне обязательны: auth + RBAC, идемпотентность входящих webhook, запись в `audit_logs`, structured JSON logging.

## Модель данных

Полные DDL пиши через Alembic-миграции. Ниже — сущности и ключевые поля (детальные типы/constraints — в ТЗ, здесь ориентир для кода).

### `leads` — карточка лида
- `lead_id` UUID PK · `external_click_id` · `geo` (SY/MA/SA…) · `language` · `dialect` (`levantine`|`moroccan_darija`|`gulf_najdi`|`other`)
- `source_channel` (`telegram_ads`|`organic`|`existing_base`|`referral`)
- `status`: `new → contacted → qualified → registered → kyc_pending → kyc_approved → ftd → active → (churned|unsubscribed)`
- `assigned_manager_id` FK users · `offer_id` FK offers · `telegram_user_id` (индекс, для матчинга с Chatterfy)
- `consent_status` (`granted`|`revoked`|`unknown`) — обязателен для лидов из существующей базы (~500k контактов)
- `created_at`, `updated_at`

### `tracking_events`
`id · lead_id (nullable) · session_id · click_id (indexed) · campaign_id · adset_id · creative_id · landing_id · event_type · event_timestamp · raw_payload (JSONB)`
`event_type` enum: `click · landing_view · lead_created · conversation_started · manager_assigned · registration · kyc · ftd · deposit · withdrawal · affiliate_commission · unsubscribe · chargeback`

### `communications`
`id · lead_id · manager_id (nullable) · channel (telegram|whatsapp|webchat) · direction (inbound|outbound) · message_text · external_message_id (indexed, идемпотентность синка с Chatterfy) · is_ai_suggested (bool, задел под будущий LLM Copilot) · created_at`

### `affiliate_events`
`id · lead_id · partner (default 'binolla') · external_event_id (UNIQUE — ключ идемпотентности) · event_type (registration|kyc_approved|ftd|deposit|withdrawal|commission|chargeback) · amount · currency · raw_payload (JSONB, храни ВСЕГДА) · normalized_payload (JSONB) · received_at · processed_at`

### `users`
`id · full_name · role (admin|tech_lead|compliance|affiliate_manager|sales_manager|smm_manager|analyst) · geo_coverage (varchar[]) · dialects (varchar[]) · telegram_id · is_active`

### `campaigns`
`id · name · geo · platform (default telegram_ads) · budget · status (draft|active|paused|archived)`

### `offers`
`id · partner_name (default Binolla) · geo · commission_model (cpa|revshare|hybrid) · status (active|paused) · api_docs_url`

### `tasks`
`id · lead_id · manager_id · title · due_at · status (open|done|cancelled)`

### `audit_logs`
`id · actor_id (nullable для системных действий) · action · entity_type · entity_id · meta (JSONB) · created_at`
**Пиши сюда на КАЖДОЕ изменяющее действие** (смена статуса лида, назначение менеджера, изменение прав и т.д.) — это требование DoD, не опция.

## Lead ID — правила (важно соблюдать при реализации)

1. UUID v4, генерируется только на backend.
2. Создаётся при первом связанном событии: клик (`tracking_events`) ИЛИ первое входящее сообщение в Chatterfy без предшествующего клика.
3. Если пришёл клик → потом написал в Telegram: сопоставление по `click_id`, переданному через deep-link/start-параметр бота.
4. Если сопоставить не удалось — новый `lead_id`, `source_channel = organic`.
5. **Не пересоздавать** `lead_id` для одного и того же пользователя — сначала искать по `telegram_user_id` / `external_click_id`.

## REST API — конвенции

Префикс `/api/v1`. JSON. Auth: Bearer JWT для пользовательских эндпоинтов, HMAC-подпись для webhook. **Курсорная пагинация** для списков (`?cursor=…&limit=…`), не offset-based.

Ключевые эндпоинты (полный список — в ТЗ):
```
POST /track/click                      signed
GET|POST /leads, GET|PATCH /leads/{id} sales_manager+ / admin
POST /leads/{id}/assign                admin, affiliate_manager
GET /leads/{id}/communications         sales_manager+
GET /dashboard/funnel, /dashboard/kpi  analyst+
POST /webhooks/binolla                 signed, без user-auth
POST /webhooks/chatterfy               signed
```

## Webhook — обязательная последовательность обработки

Для ЛЮБОГО входящего webhook (Binolla, Chatterfy) реализуй именно в этом порядке:

1. Проверить подпись/secret.
2. Провалидировать структуру payload.
3. Проверить идемпотентность по внешнему ID события (уникальный индекс в БД) — при повторе вернуть 200 без повторной обработки.
4. Определить `lead_id`.
5. Сохранить `raw_payload` ДО любой трансформации.
6. Нормализовать в internal-формат.
7. Обновить статус лида, если применимо.
8. Записать `audit_log`.
9. Вернуть корректный HTTP-код (2xx успех / 4xx ошибка валидации-подписи / 5xx временная ошибка — партнёр должен ретраить).

> ⚠️ Точные поля/заголовки/эндпоинты Binolla и Chatterfy нужно сверить с их актуальной документацией перед реализацией adapter'ов — не считай схемы ниже финальными, это нормализованный внутренний контракт.

Обработка ошибок: неизвестный `lead_id` → сохранить как `unmatched`, НЕ отбрасывать событие, эскалация Affiliate Manager. Дубликат → идемпотентный 200. Невалидная подпись → 401, событие не сохраняется, инцидент логируется отдельно.

## Auto-assignment — порядок правил

1. Совпадение `geo_coverage` менеджера с GEO лида.
2. Совпадение `dialects`.
3. Наименьшая текущая нагрузка среди подходящих.
4. Нет подходящих → лид в очередь `unassigned`, видна admin/affiliate_manager.

## RBAC — матрица прав

| Право | admin | affiliate_manager | sales_manager | compliance | analyst |
|---|---|---|---|---|---|
| Просмотр своих лидов | ✓ | ✓ | ✓ | ✓ | — |
| Просмотр всех лидов | ✓ | ✓ | — | ✓ | ✓ (без PII) |
| Редактирование лида | ✓ | ✓ | ✓ (свои) | — | — |
| Назначение менеджера | ✓ | ✓ | — | — | — |
| Просмотр revenue/commission | ✓ | ✓ | — | ✓ | ✓ |
| Управление пользователями | ✓ | — | — | — | — |
| Настройка webhook/интеграций | ✓ | — | — | — | — |
| Просмотр audit logs | ✓ | — | — | ✓ | — |

Каждый защищённый эндпоинт должен быть покрыт тестом, что запрещённая роль получает 403.

## Нефункциональные требования (не опционально)

- 2FA обязательна для роли `admin`.
- Rate limiting на `/track/click` и публичных эндпоинтах (Cloudflare + app-level).
- Секреты — только через env/secret manager, никогда в коде или БД в открытом виде.
- Ежедневные автоматические backups PostgreSQL + периодическая проверка восстановления.
- P95 latency < 300ms для чтения карточки лида и списка лидов.
- Structured JSON logging везде; Sentry на ошибки.

## Definition of Done (проверяй перед тем как считать фичу готовой)

- [ ] Lead ID не дублируется для повторных обращений.
- [ ] Клик → tracking_event → корректная связка с лидом по click_id при последующем сообщении.
- [ ] Карточка лида отдаёт все 5 блоков (профиль, acquisition, менеджер, communication, affiliate) без доработок вручную.
- [ ] Chatterfy sync идемпотентен (нет дублей при повторной доставке webhook).
- [ ] Binolla postback обрабатывается идемпотентно, `raw_payload` сохраняется всегда.
- [ ] Auto-assignment работает по правилам без ручного вмешательства в штатной ситуации.
- [ ] Dashboard показывает воронку click → commission и базовые KPI.
- [ ] RBAC покрыт тестами (403 на запрещённых действиях).
- [ ] Все изменяющие операции пишутся в audit_logs.
- [ ] Backups настроены, restore протестирован хотя бы раз.

## Порядок реализации (спринты)

1. **Sprint 0** — Docker, Postgres, миграции, CI, FastAPI-скелет, auth/JWT.
2. **Sprint 1** — модель данных + `/track/click` + Lead ID pipeline + CRUD `/leads`.
3. **Sprint 2** — карточка лида (frontend) + список/фильтры + RBAC-мидлварь.
4. **Sprint 3** — интеграция Chatterfy (webhook in/out).
5. **Sprint 4** — webhook Binolla + Event Engine + revenue attribution.
6. **Sprint 5** — auto-assignment + tasks + dashboard (funnel + KPI).
7. **Sprint 6** — audit logs + backups + нагрузочное тестирование + security review.

Двигайся по спринтам последовательно — каждый следующий зависит от Definition of Done предыдущего для соответствующих сущностей.

## Что НЕ входит в этот этап

- LLM Copilot / AI Agent (будущая фаза, отдельное ТЗ).
- Настройка рекламных кабинетов Telegram Ads.
- Юридическая/compliance-проверка GEO — считается закрытой отдельно, в коде не блокирует разработку.
