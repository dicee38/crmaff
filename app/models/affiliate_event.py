import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AffiliateEventSource, AffiliateEventType
from app.models.types import GUID, JSONBType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AffiliateEvent(Base):
    __tablename__ = "affiliate_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("leads.lead_id"), nullable=True, index=True)
    partner: Mapped[str] = mapped_column(String(64), nullable=False, default="binolla")
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    source: Mapped[AffiliateEventSource] = mapped_column(
        Enum(AffiliateEventSource, values_callable=lambda x: [e.value for e in x], native_enum=False, length=16),
        nullable=False,
        default=AffiliateEventSource.postback,
        server_default=AffiliateEventSource.postback.value,
    )
    entered_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True, index=True
    )
    channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[AffiliateEventType] = mapped_column(
        Enum(AffiliateEventType, values_callable=lambda x: [e.value for e in x], native_enum=False, length=32),
        nullable=False,
    )
    amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONBType(), nullable=False, default=dict)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONBType(), nullable=True)
    validation_flags: Mapped[dict | None] = mapped_column(JSONBType(), nullable=True)
    # Python-side default - нужна микросекундная точность для курсорной пагинации в /actions.
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
