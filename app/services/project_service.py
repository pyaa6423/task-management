from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.exceptions import NotFoundError, ConflictError


async def get_projects(db: AsyncSession, offset: int = 0, limit: int = 20) -> list[Project]:
    stmt = (
        select(Project)
        .options(selectinload(Project.tasks).selectinload(Task.children))
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await db.scalars(stmt)).all())


async def get_project(db: AsyncSession, project_id: int) -> Project:
    stmt = (
        select(Project)
        .options(selectinload(Project.tasks).selectinload(Task.children))
        .where(Project.id == project_id)
    )
    project = await db.scalar(stmt)
    if not project:
        raise NotFoundError("Project", project_id)
    return project


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return await get_project(db, project.id)


async def update_project(db: AsyncSession, project_id: int, data: ProjectUpdate) -> Project:
    project = await get_project(db, project_id)
    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_completed") is True and not project.is_completed:
        # Check for incomplete tasks
        for task in project.tasks:
            if not task.is_completed:
                raise ConflictError(
                    f"Cannot complete project: task '{task.title}' is not completed"
                )
        update_data["completed_at"] = datetime.now(timezone.utc)
    elif update_data.get("is_completed") is False:
        update_data["completed_at"] = None

    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    return await get_project(db, project.id)


async def delete_project(db: AsyncSession, project_id: int) -> None:
    project = await get_project(db, project_id)
    await db.delete(project)
    await db.commit()
