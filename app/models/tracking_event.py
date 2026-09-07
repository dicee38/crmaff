import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import TrackingEventType
from app.models.types import GUID, JSONBType


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("leads.lead_id"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    click_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    adset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    creative_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    landing_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    event_type: Mapped[TrackingEventType] = mapped_column(
        Enum(TrackingEventType, values_callable=lambda x: [e.value for e in x], native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    raw_payload: Mapped[dict] = mapped_column(JSONBType(), nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
