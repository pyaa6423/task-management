from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subtask import SubTask
from app.models.task import Task
from app.schemas.subtask import SubTaskCreate, SubTaskUpdate
from app.exceptions import NotFoundError


async def get_subtasks_by_task(db: AsyncSession, task_id: int) -> list[SubTask]:
    task = await db.get(Task, task_id)
    if not task:
        raise NotFoundError("Task", task_id)

    stmt = (
        select(SubTask)
        .where(SubTask.task_id == task_id)
        .order_by(SubTask.priority.asc())
    )
    return list((await db.scalars(stmt)).all())


async def get_subtask(db: AsyncSession, subtask_id: int) -> SubTask:
    subtask = await db.get(SubTask, subtask_id)
    if not subtask:
        raise NotFoundError("SubTask", subtask_id)
    return subtask


async def create_subtask(db: AsyncSession, task_id: int, data: SubTaskCreate) -> SubTask:
    task = await db.get(Task, task_id)
    if not task:
        raise NotFoundError("Task", task_id)

    subtask = SubTask(task_id=task_id, **data.model_dump())
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)
    return subtask


async def update_subtask(db: AsyncSession, subtask_id: int, data: SubTaskUpdate) -> SubTask:
    subtask = await get_subtask(db, subtask_id)
    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_completed") is True and not subtask.is_completed:
        update_data["completed_at"] = datetime.now(timezone.utc)
    elif update_data.get("is_completed") is False:
        update_data["completed_at"] = None

    for key, value in update_data.items():
        setattr(subtask, key, value)

    await db.commit()
    await db.refresh(subtask)
    return subtask


async def delete_subtask(db: AsyncSession, subtask_id: int) -> None:
    subtask = await get_subtask(db, subtask_id)
    await db.delete(subtask)
    await db.commit()
