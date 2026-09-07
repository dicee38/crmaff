import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


async def get_lead(db: AsyncSession, lead_id: uuid.UUID) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.lead_id == lead_id))
    return result.scalar_one_or_none()


async def get_lead_by_telegram_user_id(db: AsyncSession, telegram_user_id: str) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.telegram_user_id == telegram_user_id))
    return result.scalar_one_or_none()


async def get_lead_by_external_click_id(db: AsyncSession, external_click_id: str) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.external_click_id == external_click_id))
    return result.scalar_one_or_none()


async def list_leads(
    db: AsyncSession,
    *,
    cursor: datetime | None = None,
    limit: int = 50,
    manager_id: uuid.UUID | None = None,
    geo: str | None = None,
    status: str | None = None,
) -> list[Lead]:
    query = select(Lead).order_by(Lead.created_at.desc(), Lead.lead_id.desc())

    if cursor is not None:
        query = query.where(Lead.created_at < cursor)
    if manager_id is not None:
        query = query.where(Lead.assigned_manager_id == manager_id)
    if geo is not None:
        query = query.where(Lead.geo == geo)
    if status is not None:
        query = query.where(Lead.status == status)

    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_lead(db: AsyncSession, data: LeadCreate) -> Lead:
    lead = Lead(
        lead_id=uuid.uuid4(),
        external_click_id=data.external_click_id,
        geo=data.geo,
        language=data.language,
        dialect=data.dialect,
        source_channel=data.source_channel,
        telegram_user_id=data.telegram_user_id,
        offer_id=data.offer_id,
        consent_status=data.consent_status,
    )
    db.add(lead)
    await db.flush()
    return lead


async def update_lead(db: AsyncSession, lead: Lead, data: LeadUpdate) -> Lead:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    lead.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return lead
