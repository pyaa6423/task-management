from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.task import Task
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate
from app.exceptions import NotFoundError, ConflictError


def _children_load():
    """Recursive eager loading for children (2 levels deep)."""
    return selectinload(Task.children).selectinload(Task.children)


async def get_tasks_by_project(db: AsyncSession, project_id: int) -> list[Task]:
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    stmt = (
        select(Task)
        .options(_children_load())
        .where(Task.project_id == project_id, Task.parent_id.is_(None))
        .order_by(Task.priority.asc())
    )
    return list((await db.scalars(stmt)).all())


async def get_task(db: AsyncSession, task_id: int) -> Task:
    stmt = (
        select(Task)
        .options(_children_load())
        .where(Task.id == task_id)
    )
    task = await db.scalar(stmt)
    if not task:
        raise NotFoundError("Task", task_id)
    return task


async def create_task(db: AsyncSession, project_id: int, data: TaskCreate, parent_id: int | None = None) -> Task:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    if parent_id is not None:
        parent = await db.get(Task, parent_id)
        if not parent:
            raise NotFoundError("Task", parent_id)
        # Auto-uncomplete parent if it was completed
        if parent.is_completed:
            parent.is_completed = False
            parent.completed_at = None

    task = Task(project_id=project_id, parent_id=parent_id, **data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return await get_task(db, task.id)


async def update_task(db: AsyncSession, task_id: int, data: TaskUpdate) -> Task:
    db.expire_all()
    task = await get_task(db, task_id)
    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_completed") is True and not task.is_completed:
        # Check for incomplete children
        for child in task.children:
            if not child.is_completed:
                raise ConflictError(
                    f"Cannot complete task: child task '{child.title}' is not completed"
                )
        update_data["completed_at"] = datetime.now(timezone.utc)
    elif update_data.get("is_completed") is False:
        update_data["completed_at"] = None

    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()

    # Auto-complete parent if all siblings are now complete
    if task.parent_id and task.is_completed:
        parent_id = task.parent_id
        db.expire_all()
        stmt = (
            select(Task)
            .options(selectinload(Task.children))
            .where(Task.id == parent_id)
        )
        parent = await db.scalar(stmt)
        if parent and not parent.is_completed:
            all_done = all(c.is_completed for c in parent.children)
            if all_done:
                parent.is_completed = True
                parent.completed_at = datetime.now(timezone.utc)
                await db.commit()

    return await get_task(db, task_id)


async def delete_task(db: AsyncSession, task_id: int) -> None:
    task = await get_task(db, task_id)
    await db.delete(task)
    await db.commit()


async def get_children(db: AsyncSession, task_id: int) -> list[Task]:
    # Verify parent task exists
    parent = await db.get(Task, task_id)
    if not parent:
        raise NotFoundError("Task", task_id)

    stmt = (
        select(Task)
        .options(_children_load())
        .where(Task.parent_id == task_id)
        .order_by(Task.priority.asc())
    )
    return list((await db.scalars(stmt)).all())
