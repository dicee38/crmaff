import base64
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rbac import CAN_VIEW_ALL_LEADS
from app.crud.lead import get_lead
from app.crud.task import create_task, get_task, list_tasks, update_task
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.task import TaskCreate, TaskListResponse, TaskOut, TaskUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _encode_cursor(dt: datetime) -> str:
    return base64.urlsafe_b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    try:
        return datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor") from exc


def _assert_can_view_task(current_user: User, task) -> None:
    if current_user.role in CAN_VIEW_ALL_LEADS:
        return
    if current_user.role == UserRole.sales_manager and task.manager_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def _assert_can_edit_task(current_user: User, task) -> None:
    if current_user.role in (UserRole.admin, UserRole.affiliate_manager):
        return
    if current_user.role == UserRole.sales_manager and task.manager_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


@router.get("", response_model=TaskListResponse)
async def list_tasks_endpoint(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    lead_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    decoded_cursor = _decode_cursor(cursor) if cursor else None

    manager_filter = None
    if current_user.role not in CAN_VIEW_ALL_LEADS:
        if current_user.role != UserRole.sales_manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        manager_filter = current_user.id

    tasks = await list_tasks(
        db,
        cursor=decoded_cursor,
        limit=limit + 1,
        manager_id=manager_filter,
        lead_id=lead_id,
        status=status_filter,
    )

    next_cursor = None
    if len(tasks) > limit:
        tasks = tasks[:limit]
        next_cursor = _encode_cursor(tasks[-1].created_at)

    return TaskListResponse(items=[TaskOut.model_validate(t) for t in tasks], next_cursor=next_cursor)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    lead = await get_lead(db, payload.lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    can_create = current_user.role in (UserRole.admin, UserRole.affiliate_manager) or (
        current_user.role == UserRole.sales_manager and lead.assigned_manager_id == current_user.id
    )
    if not can_create:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    task = await create_task(db, payload, default_manager_id=current_user.id)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="task_created",
        entity_type="task",
        entity_id=str(task.id),
        meta={"lead_id": str(task.lead_id), "title": task.title},
    )
    await db.commit()
    return TaskOut.model_validate(task)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task_endpoint(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _assert_can_view_task(current_user, task)
    return TaskOut.model_validate(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task_endpoint(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _assert_can_edit_task(current_user, task)

    before = {"status": task.status.value, "manager_id": str(task.manager_id)}
    task = await update_task(db, task, payload)

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="task_updated",
        entity_type="task",
        entity_id=str(task.id),
        meta={"before": before, "changes": payload.model_dump(mode="json", exclude_unset=True)},
    )
    await db.commit()
    return TaskOut.model_validate(task)
