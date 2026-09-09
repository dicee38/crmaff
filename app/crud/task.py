import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    *,
    cursor: datetime | None = None,
    limit: int = 50,
    manager_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[Task]:
    query = select(Task).order_by(Task.created_at.desc(), Task.id.desc())

    if cursor is not None:
        query = query.where(Task.created_at < cursor)
    if manager_id is not None:
        query = query.where(Task.manager_id == manager_id)
    if lead_id is not None:
        query = query.where(Task.lead_id == lead_id)
    if status is not None:
        query = query.where(Task.status == status)

    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_task(db: AsyncSession, data: TaskCreate, *, default_manager_id: uuid.UUID | None) -> Task:
    task = Task(
        id=uuid.uuid4(),
        lead_id=data.lead_id,
        manager_id=data.manager_id if data.manager_id is not None else default_manager_id,
        title=data.title,
        due_at=data.due_at,
    )
    db.add(task)
    await db.flush()
    return task


async def update_task(db: AsyncSession, task: Task, data: TaskUpdate) -> Task:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return task
