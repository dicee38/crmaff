import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import CampaignStatus
from app.models.types import GUID


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geo: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, default="telegram_ads")
    budget: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, values_callable=lambda x: [e.value for e in x], native_enum=False, length=32),
        nullable=False,
        default=CampaignStatus.draft,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
