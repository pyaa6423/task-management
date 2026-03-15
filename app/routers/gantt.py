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


def _task_to_gantt(task, children=None):
    if children is None:
        children = getattr(task, "children", [])
    completed = sum(1 for c in children if c.is_completed)
    total = len(children)
    progress = (completed / total * 100) if total > 0 else (100 if task.is_completed else 0)
    return {
        "id": f"task-{task.id}",
        "name": task.title,
        "start": task.start_time.isoformat() if task.start_time else None,
        "end": task.end_time.isoformat() if task.end_time else None,
        "progress": progress,
        "priority": task.priority,
        "is_completed": task.is_completed,
        "has_children": total > 0,
        "completed_count": completed,
        "total_count": total,
        "assigned_member": task.assigned_member,
    }


@router.get("/gantt", response_class=HTMLResponse)
async def gantt_page(request: Request, db: AsyncSession = Depends(get_db)):
    projects = (await db.scalars(select(Project).order_by(Project.created_at.desc()))).all()
    return templates.TemplateResponse(request, "gantt.html", {"projects": projects})


@router.get("/api/v1/gantt/overview")
async def gantt_overview(db: AsyncSession = Depends(get_db)):
    """All projects with their top-level tasks for overview display."""
    projects = (await db.scalars(
        select(Project).order_by(Project.created_at.desc())
    )).all()

    result = []
    for project in projects:
        stmt = (
            select(Task)
            .options(selectinload(Task.children))
            .where(Task.project_id == project.id, Task.parent_id.is_(None))
            .order_by(Task.priority.asc())
        )
        tasks = (await db.scalars(stmt)).all()
        result.append({
            "id": project.id,
            "name": project.name,
            "start_date": str(project.start_date) if project.start_date else None,
            "end_date": str(project.end_date) if project.end_date else None,
            "is_completed": project.is_completed,
            "tasks": [_task_to_gantt(t) for t in tasks],
        })
    return result


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
    return [_task_to_gantt(t) for t in tasks]


@router.get("/api/v1/gantt/tasks/{task_id}/children")
async def gantt_task_children(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    # Get parent task with its children
    parent_stmt = (
        select(Task)
        .options(selectinload(Task.children).selectinload(Task.children))
        .where(Task.id == task_id)
    )
    parent = await db.scalar(parent_stmt)
    if not parent:
        return {"parent": None, "children": []}

    return {
        "parent": _task_to_gantt(parent),
        "children": [_task_to_gantt(c) for c in sorted(parent.children, key=lambda c: c.priority)],
    }
