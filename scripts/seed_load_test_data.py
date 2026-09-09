"""Генерирует синтетический датасет для нагрузочного тестирования.

Использование:
    python scripts/seed_load_test_data.py --leads 20000

Создаёт менеджеров (sales_manager с разным geo_coverage/dialects) и лидов
с реалистичным распределением по GEO/статусу/менеджеру, плюс tracking_events
и affiliate_events на часть лидов - чтобы GET /leads/{id}/card не тестировался
на пустых JOIN'ах.
"""

import argparse
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from app.crud.user import get_user_by_email
from app.database import AsyncSessionLocal
from app.models.affiliate_event import AffiliateEvent
from app.models.enums import (
    AffiliateEventSource,
    AffiliateEventType,
    ConsentStatus,
    Dialect,
    LeadStatus,
    SourceChannel,
    TrackingEventType,
    UserRole,
)
from app.models.lead import Lead
from app.models.tracking_event import TrackingEvent
from app.models.user import User
from app.core.security import hash_password

GEOS = ["SY", "MA", "SA"]
GEO_DIALECT = {"SY": Dialect.levantine, "MA": Dialect.moroccan_darija, "SA": Dialect.gulf_najdi}
STATUSES = list(LeadStatus)
STATUS_WEIGHTS = [30, 15, 10, 15, 8, 7, 8, 5, 1, 1]  # больше "new", меньше глубоких стадий


async def _ensure_managers(db, n: int = 10) -> list[User]:
    managers = []
    for i in range(n):
        email = f"loadtest-manager-{i}@example.com"
        existing = await get_user_by_email(db, email)
        if existing:
            managers.append(existing)
            continue
        geo = GEOS[i % len(GEOS)]
        user = User(
            id=uuid.uuid4(),
            full_name=f"Load Test Manager {i}",
            email=email,
            hashed_password=hash_password("secret123"),
            role=UserRole.sales_manager,
            geo_coverage=[geo],
            dialects=[GEO_DIALECT[geo].value],
        )
        db.add(user)
        managers.append(user)
    await db.flush()
    return managers


async def seed(total_leads: int, batch_size: int = 1000) -> None:
    async with AsyncSessionLocal() as db:
        managers = await _ensure_managers(db)
        await db.commit()

    created = 0
    while created < total_leads:
        batch = min(batch_size, total_leads - created)
        async with AsyncSessionLocal() as db:
            leads = []
            for _ in range(batch):
                geo = random.choice(GEOS)
                status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
                created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
                manager = random.choice(managers) if random.random() < 0.7 else None

                lead = Lead(
                    lead_id=uuid.uuid4(),
                    external_click_id=f"loadtest-click-{uuid.uuid4().hex[:12]}",
                    geo=geo,
                    language="ar",
                    dialect=GEO_DIALECT[geo],
                    source_channel=random.choice(list(SourceChannel)),
                    status=status,
                    assigned_manager_id=manager.id if manager else None,
                    consent_status=random.choice(list(ConsentStatus)),
                    created_at=created_at,
                    updated_at=created_at,
                )
                leads.append((lead, created_at))
                db.add(lead)

            # Без явного relationship() SQLAlchemy не гарантирует порядок INSERT
            # между таблицами - сначала фиксируем лидов, потом зависимые записи,
            # иначе FK-нарушение (affiliate_events/tracking_events -> leads).
            await db.flush()

            for lead, created_at in leads:
                if random.random() < 0.5:
                    db.add(
                        TrackingEvent(
                            id=uuid.uuid4(),
                            lead_id=lead.lead_id,
                            event_type=TrackingEventType.click,
                            click_id=lead.external_click_id,
                            campaign_id=f"camp-{random.randint(1, 20)}",
                            event_timestamp=created_at,
                            raw_payload={"seed": True},
                        )
                    )
                if lead.status in (LeadStatus.ftd, LeadStatus.active) and random.random() < 0.8:
                    db.add(
                        AffiliateEvent(
                            id=uuid.uuid4(),
                            lead_id=lead.lead_id,
                            partner="binolla",
                            external_event_id=f"loadtest:{uuid.uuid4()}",
                            event_type=AffiliateEventType.ftd,
                            source=AffiliateEventSource.postback,
                            amount=round(random.uniform(20, 500), 2),
                            currency="USD",
                            raw_payload={"seed": True},
                            received_at=created_at,
                        )
                    )

            await db.commit()

        created += batch
        print(f"[seed] {created}/{total_leads}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--leads", type=int, default=20000)
    args = parser.parse_args()
    asyncio.run(seed(args.leads))
