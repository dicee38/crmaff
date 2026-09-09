"""Auto-assignment лида на менеджера.

Правила (см. CLAUDE.md, раздел "Auto-assignment — порядок правил"):
1. Совпадение geo_coverage менеджера с GEO лида.
2. Совпадение dialects.
3. Наименьшая текущая нагрузка среди подходящих.
4. Нет подходящих -> лид остаётся unassigned (видна admin/affiliate_manager
   через фильтр assigned=false в GET /leads).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.lead import Lead
from app.models.user import User


async def _find_candidates(db: AsyncSession, lead: Lead) -> list[User]:
    if not lead.geo:
        return []

    result = await db.execute(
        select(User).where(User.role == UserRole.sales_manager, User.is_active.is_(True))
    )
    all_managers = list(result.scalars().all())

    # Правило 1: geo_coverage.
    geo_matched = [u for u in all_managers if lead.geo in u.geo_coverage]
    if not geo_matched:
        return []

    # Правило 2: dialects (только если у лида известен диалект).
    if lead.dialect is not None:
        dialect_matched = [u for u in geo_matched if lead.dialect.value in u.dialects]
        if dialect_matched:
            return dialect_matched
        return []

    return geo_matched


async def _current_load(db: AsyncSession, manager_id) -> int:
    result = await db.execute(select(func.count()).select_from(Lead).where(Lead.assigned_manager_id == manager_id))
    return result.scalar_one()


async def try_auto_assign(db: AsyncSession, lead: Lead) -> User | None:
    """Пытается назначить менеджера на лида. Не трогает уже назначенных лидов.

    Возвращает назначенного User или None, если подходящих не нашлось
    (лид остаётся в очереди unassigned - правило 4).
    """
    if lead.assigned_manager_id is not None:
        return None

    candidates = await _find_candidates(db, lead)
    if not candidates:
        return None

    # Правило 3: наименьшая текущая нагрузка среди подходящих.
    loads = [(await _current_load(db, u.id), u) for u in candidates]
    loads.sort(key=lambda pair: pair[0])
    best_manager = loads[0][1]

    lead.assigned_manager_id = best_manager.id
    await db.flush()
    return best_manager
