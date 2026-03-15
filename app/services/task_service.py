from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.task import Task
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate
from app.exceptions import NotFoundError, ConflictError


async def get_tasks_by_project(db: AsyncSession, project_id: int) -> list[Task]:
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    stmt = (
        select(Task)
        .options(selectinload(Task.subtasks))
        .where(Task.project_id == project_id)
        .order_by(Task.priority.asc())
    )
    return list((await db.scalars(stmt)).all())


async def get_task(db: AsyncSession, task_id: int) -> Task:
    stmt = (
        select(Task)
        .options(selectinload(Task.subtasks))
        .where(Task.id == task_id)
    )
    task = await db.scalar(stmt)
    if not task:
        raise NotFoundError("Task", task_id)
    return task


async def create_task(db: AsyncSession, project_id: int, data: TaskCreate) -> Task:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    task = Task(project_id=project_id, **data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return await get_task(db, task.id)


async def update_task(db: AsyncSession, task_id: int, data: TaskUpdate) -> Task:
    task = await get_task(db, task_id)
    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_completed") is True and not task.is_completed:
        # Check for incomplete subtasks
        for subtask in task.subtasks:
            if not subtask.is_completed:
                raise ConflictError(
                    f"Cannot complete task: subtask '{subtask.title}' is not completed"
                )
        update_data["completed_at"] = datetime.now(timezone.utc)
    elif update_data.get("is_completed") is False:
        update_data["completed_at"] = None

    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    return await get_task(db, task_id)


async def delete_task(db: AsyncSession, task_id: int) -> None:
    task = await get_task(db, task_id)
    await db.delete(task)
    await db.commit()
