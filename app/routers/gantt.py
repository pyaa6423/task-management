from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.database import get_db
from app.models.task import Task
from app.models.project import Project

router = APIRouter(tags=["gantt"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/gantt", response_class=HTMLResponse)
async def gantt_page(request: Request, db: AsyncSession = Depends(get_db)):
    projects = (await db.scalars(select(Project).order_by(Project.created_at.desc()))).all()
    return templates.TemplateResponse(request, "gantt.html", {"projects": projects})


@router.get("/api/v1/gantt/projects/{project_id}")
async def gantt_project_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Task)
        .options(selectinload(Task.children))
        .where(Task.project_id == project_id, Task.parent_id.is_(None))
        .order_by(Task.priority.asc())
    )
    tasks = (await db.scalars(stmt)).all()

    result = []
    for task in tasks:
        completed_children = sum(1 for c in task.children if c.is_completed)
        total_children = len(task.children)
        progress = (completed_children / total_children * 100) if total_children > 0 else 0

        result.append({
            "id": f"task-{task.id}",
            "name": task.title,
            "start": task.start_time.isoformat() if task.start_time else None,
            "end": task.end_time.isoformat() if task.end_time else None,
            "progress": progress,
            "priority": task.priority,
            "is_completed": task.is_completed,
            "has_children": total_children > 0,
        })
    return result


@router.get("/api/v1/gantt/tasks/{task_id}/children")
async def gantt_task_children(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Task)
        .options(selectinload(Task.children))
        .where(Task.parent_id == task_id)
        .order_by(Task.priority.asc())
    )
    children = (await db.scalars(stmt)).all()

    return [
        {
            "id": f"task-{c.id}",
            "name": c.title,
            "start": c.start_time.isoformat() if c.start_time else None,
            "end": c.end_time.isoformat() if c.end_time else None,
            "progress": 100 if c.is_completed else 0,
            "priority": c.priority,
            "is_completed": c.is_completed,
            "has_children": len(c.children) > 0,
        }
        for c in children
    ]
