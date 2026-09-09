import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import CommissionModel, OfferStatus
from app.models.types import GUID


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Binolla")
    geo: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    commission_model: Mapped[CommissionModel] = mapped_column(
        Enum(CommissionModel, values_callable=lambda x: [e.value for e in x], native_enum=False, length=32),
        nullable=False,
    )
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, values_callable=lambda x: [e.value for e in x], native_enum=False, length=32),
        nullable=False,
        default=OfferStatus.active,
    )
    api_docs_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Шаблон ссылки для 302-редиректа с click-эндпоинта на оффер партнёра.
    # Содержит плейсхолдер {click_id}, напр.:
    # "https://binolla.com/?lid=28941&click_id={click_id}&site_id=1"
    # Точный формат (какие параметры кроме click_id нужны) задаётся партнёром
    # в его личном кабинете ("Link format") - см. CLAUDE.md, сверять перед прод-использованием.
    redirect_url_template: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
