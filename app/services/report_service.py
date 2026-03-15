from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.task import Task
from app.models.project import Project
from app.schemas.report import CompletedItemResponse


async def get_completed_items(
    db: AsyncSession,
    start: datetime,
    end: datetime,
    member: str | None = None,
) -> list[CompletedItemResponse]:
    items: list[CompletedItemResponse] = []

    # Completed tasks in range
    task_stmt = (
        select(Task)
        .options(selectinload(Task.project), selectinload(Task.parent))
        .where(Task.completed_at >= start, Task.completed_at < end)
    )
    if member:
        task_stmt = task_stmt.where(Task.assigned_member == member)
    tasks = (await db.scalars(task_stmt)).all()

    for task in tasks:
        items.append(CompletedItemResponse(
            item_type="task",
            title=task.title,
            project_name=task.project.name,
            parent_task_title=task.parent.title if task.parent else None,
            assigned_member=task.assigned_member,
            completed_at=task.completed_at,
        ))

    items.sort(key=lambda x: x.completed_at)
    return items
