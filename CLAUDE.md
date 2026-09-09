# CLAUDE.md — CRM affiliate-платформы

Этот файл — контекст проекта для Claude Code. Читай его перед началом любой задачи в этом репозитории. Полное ТЗ (с обоснованиями и деталями) — `docs/tz-crm.docx` / см. историю чата; здесь — только то, что нужно держать в контексте при написании кода.

## Что это за проект

CRM-подсистема affiliate-платформы для арабоязычного трафика.
Вертикаль: Forex / бинарные опционы. Партнёр: **Binolla**.
Стартовые GEO: **Сирия (Levantine Arabic), Марокко (Moroccan Darija), Саудовская Аравия (Gulf/Najdi Arabic)**.
Коммуникация с лидами — через **Chatterfy** (Telegram CRM), поверх уже существующей webhook-интеграции на FastAPI/Railway.

Сквозная цепочка, которую должна поддерживать система:
`Click → Lead ID → Manager → Registration → Target Event (FTD) → Commission → Analytics`

Дополнительно (см. отдельные разделы ниже): ручной ввод действий менеджеров, cashflow-отчётность по МОП и лидерборд — по образцу уже знакомого командного функционала (аналог Jarvis Fin ERP / BinOne), адаптированный под нашу схему `affiliate_events`.

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
`id · lead_id · partner (default 'binolla') · external_event_id (UNIQUE — ключ идемпотентности для postback; для ручных записей — генерируется как manual:<uuid>) · source (postback|manual) · entered_by (FK users, nullable — только для manual) · channel (varchar, nullable — канал/саб-группа, напр. "MENA-KARIM") · event_type (registration|kyc_approved|ftd|deposit|withdrawal|commission|chargeback) · amount · currency · raw_payload (JSONB, для manual — сериализованные поля формы) · normalized_payload (JSONB) · validation_flags (JSONB, nullable — предупреждения/ошибки валидации ручной записи) · received_at · processed_at`

### `users`
`id · full_name · role (admin|tech_lead|compliance|affiliate_manager|mop_lead|sales_manager|smm_manager|analyst) · geo_coverage (varchar[]) · dialects (varchar[]) · telegram_id · is_active`

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

## Ручной ввод действий МОП (Manual Action Entry)

Помимо автоматического postback от партнёра (Binolla), менеджер (МОП) должен уметь **вручную** внести действие игрока — например, если конверсия не пришла по API, партнёр её не поддерживает, или нужно скорректировать данные. Это пишется в ту же таблицу `affiliate_events`, но с `source = 'manual'`.

**Форма ввода — обязательные и опциональные поля:**
- ID игрока (обязательно) — сопоставляется с `lead_id` по `external_click_id`/`telegram_user_id`, как обычно
- Партнёрская сеть (select, не хардкодить только Binolla — брать из `offers.partner_name`)
- Канал (текст/select — напр. "MENA-KARIM"; группируется в отчётах как `channel`)
- Тип действия (`registration | ftd | deposit(RD) | withdrawal | chargeback`)
- Сумма (обязательно для FD/RD/withdrawal)
- Дата действия (по умолчанию — сейчас, можно указать прошедшую дату задним числом)

**Валидация при сохранении:**
- Если `lead_id` не сопоставился — запись всё равно сохраняется (не блокировать ввод менеджеру), но помечается `validation_flags: { unmatched_lead: true }` и подсвечивается в списке как предупреждение
- Дубликат (тот же игрок + тип действия + сумма + дата) — не блокируется автоматически, но помечается `validation_flags: { possible_duplicate: true }` для ручной проверки (в отличие от postback, здесь нет строгой идемпотентности по внешнему ID — сам ID генерируется на нашей стороне)
- Все ошибки/предупреждения хранятся в `validation_flags` и отображаются в списке действий отдельными колонками ("Предупреждения", "Ошибки"), не блокируя работу МОП

**Список действий (`/actions`)** — фильтруемый журнал всех записей affiliate_events (и manual, и postback вместе), с фильтрами: ID записи, диапазон дат, ID игрока, тип действия, диапазон суммы, источник (все / только API / только ручные). Наверху списка — агрегированные счётчики за выбранный период и фильтр: всего действий, кол-во лидов, кол-во депозитов, сумма депозитов.

## Cashflow-отчётность по МОП

Агрегированный отчёт по менеджерам за период — отдельный от базового `/dashboard/funnel` (тот — по всей воронке и GEO, этот — фокус на эффективности конкретных МОП).

**Группировки:** по МОП, по месяцу/неделе, по каналу и группе каналов (свободная группировка, не только GEO).

**Метрики в отчёте:**
- `REG` — количество регистраций за период
- `FD` — количество первых депозитов + сумма (`FD_count`, `FD_sum`)
- `RD` — количество повторных депозитов + сумма (`RD_count`, `RD_sum`)
- `Касса` (Cashflow) — `FD_sum + RD_sum` за период
- `Lead2Reg` — конверсия лид → регистрация, %
- `Reg2FD` — конверсия регистрация → первый депозит, %

Отчёт должен поддерживать древовидную группировку (общий итог сверху, разбивка по МОП ниже — как в дереве с раскрытием строки) и роль-зависимую видимость: `sales_manager` видит только свои данные, `mop_lead`/`admin`/`analyst` — по всей команде.

## Лидерборд (геймификация)

Рейтинг МОП по нескольким метрикам, обновляется в реальном времени, с переключением период (по неделям / по месяцам) и фильтром по группе каналов.

**Метрики лидерборда** (отдельные вкладки, каждая — самостоятельный рейтинг):
- Касса (FD + RD за период)
- Выручка FD на лид (FD_sum / кол-во лидов)
- Конверсия Lead → FD
- Конверсия FD → RD

**Отображение:**
- Топ-3 — с бейджами (золото/серебро/бронза)
- Средние позиции (напр. 4–6) сворачиваются в "Позиции N–M скрыты", чтобы не перегружать список
- Позиция текущего пользователя всегда видна с соседями по рейтингу (на 1 выше и на 1 ниже), с явным выделением ("Вы")
- Для текущего пользователя показывать дельту: сколько не хватает до следующей позиции и на сколько опережает предыдущую

**Права:** `sales_manager` видит лидерборд целиком (это мотивационный инструмент — рейтинг открыт всей команде), но карточки/детали чужих лидов недоступны, только агрегированное значение метрики.

## REST API — конвенции

Префикс `/api/v1`. JSON. Auth: Bearer JWT для пользовательских эндпоинтов, HMAC-подпись для webhook. **Курсорная пагинация** для списков (`?cursor=…&limit=…`), не offset-based.

Ключевые эндпоинты (полный список — в ТЗ):
```
POST /track/click                      signed
GET|POST /leads, GET|PATCH /leads/{id} sales_manager+ / admin
POST /leads/{id}/assign                admin, affiliate_manager
GET /leads/{id}/communications         sales_manager+
GET /dashboard/funnel, /dashboard/kpi  analyst+
POST /actions                          sales_manager+ (ручной ввод действия МОП)
GET /actions                           sales_manager+ (свои), mop_lead/admin/analyst (все)
GET /reports/mop-cashflow              mop_lead+/analyst+ (агрегированный отчёт по МОП)
GET /leaderboard                       sales_manager+ (metric, period, channel_group — см. раздел «Лидерборд»)
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

| Право | admin | affiliate_manager | mop_lead | sales_manager | compliance | analyst |
|---|---|---|---|---|---|---|
| Просмотр своих лидов | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Просмотр всех лидов | ✓ | ✓ | ✓ (своя команда) | — | ✓ | ✓ (без PII) |
| Редактирование лида | ✓ | ✓ | — | ✓ (свои) | — | — |
| Назначение менеджера | ✓ | ✓ | — | — | — | — |
| Просмотр revenue/commission | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Ручной ввод действия (`/actions`) | ✓ | ✓ | ✓ | ✓ | — | — |
| Cashflow-отчёт по команде | ✓ | ✓ | ✓ | — | — | ✓ |
| Лидерборд | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Управление пользователями | ✓ | — | — | — | — | — |
| Настройка webhook/интеграций | ✓ | — | — | — | — | — |
| Просмотр audit logs | ✓ | — | — | — | ✓ | — |

`mop_lead` — руководитель группы МОП: видит данные и лидерборд по своей команде, но не управляет пользователями и интеграциями (в отличие от `admin`/`affiliate_manager`).

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
- [ ] Ручной ввод действия (`/actions`) работает с валидацией (unmatched_lead, possible_duplicate — не блокируют сохранение, только помечают).
- [ ] Cashflow-отчёт по МОП считает REG/FD/RD/Касса/Lead2Reg/Reg2FD корректно и с ролевой видимостью.
- [ ] Лидерборд обновляется по всем 4 метрикам, топ-3 и позиция пользователя отображаются корректно.
- [ ] RBAC покрыт тестами (403 на запрещённых действиях).
- [ ] Все изменяющие операции пишутся в audit_logs.
- [ ] Backups настроены, restore протестирован хотя бы раз.

## Порядок реализации (спринты)

1. **Sprint 0** — Docker, Postgres, миграции, CI, FastAPI-скелет, auth/JWT.
2. **Sprint 1** — модель данных + `/track/click` + Lead ID pipeline + CRUD `/leads`.
3. **Sprint 2** — карточка лида (frontend) + список/фильтры + RBAC-мидлварь.
4. **Sprint 3** — интеграция Chatterfy (webhook in/out).
5. **Sprint 4** — webhook Binolla + Event Engine + revenue attribution.
6. **Sprint 5** — auto-assignment + tasks + dashboard (funnel + KPI) + ручной ввод действий (`/actions`) + cashflow-отчёт по МОП + лидерборд.
7. **Sprint 6** — audit logs + backups + нагрузочное тестирование + security review.

Двигайся по спринтам последовательно — каждый следующий зависит от Definition of Done предыдущего для соответствующих сущностей.

## Что НЕ входит в этот этап

- LLM Copilot / AI Agent (будущая фаза, отдельное ТЗ).
- Настройка рекламных кабинетов Telegram Ads.
- Юридическая/compliance-проверка GEO — считается закрытой отдельно, в коде не блокирует разработку.
