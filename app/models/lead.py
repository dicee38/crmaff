import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ConsentStatus, Dialect, LeadStatus, SourceChannel
from app.models.types import GUID


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"

    lead_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    external_click_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    geo: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    dialect: Mapped[Dialect | None] = mapped_column(
        Enum(Dialect, values_callable=_enum_values, native_enum=False, length=32),
        nullable=True,
    )

    source_channel: Mapped[SourceChannel] = mapped_column(
        Enum(SourceChannel, values_callable=_enum_values, native_enum=False, length=32),
        nullable=False,
        default=SourceChannel.organic,
    )

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, values_callable=_enum_values, native_enum=False, length=32),
        nullable=False,
        default=LeadStatus.new,
        index=True,
    )

    assigned_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True, index=True
    )
    offer_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("offers.id"), nullable=True, index=True
    )
    telegram_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    consent_status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus, values_callable=_enum_values, native_enum=False, length=32),
        nullable=False,
        default=ConsentStatus.unknown,
    )

    # Python-side default (не server_default) - нужна микросекундная точность для курсорной
    # пагинации: у SQLite/Postgres CURRENT_TIMESTAMP разрешение всего до секунды.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
