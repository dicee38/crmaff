import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import CommunicationChannel, CommunicationDirection
from app.models.types import GUID


class Communication(Base):
    __tablename__ = "communications"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("leads.lead_id"), nullable=False, index=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)

    channel: Mapped[CommunicationChannel] = mapped_column(
        Enum(CommunicationChannel, values_callable=lambda x: [e.value for e in x], native_enum=False, length=32),
        nullable=False,
    )
    direction: Mapped[CommunicationDirection] = mapped_column(
        Enum(CommunicationDirection, values_callable=lambda x: [e.value for e in x], native_enum=False, length=16),
        nullable=False,
    )
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    is_ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
