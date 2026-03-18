from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.exceptions import NotFoundError
from app.services import task_service
from app.models.task import Task
from app.models.project import Project

router = APIRouter(tags=["task_pages"])
templates = Jinja2Templates(directory="app/templates")


def _flatten_tasks(tasks: list, depth: int = 0, exclude_id: int | None = None) -> list[dict]:
    """Flatten task tree into a list with depth for indentation."""
    result: list[dict] = []
    for t in tasks:
        if t.id == exclude_id:
            continue
        prefix = "─" * depth + " " if depth > 0 else ""
        result.append({"id": t.id, "title": f"{prefix}{t.title}", "depth": depth})
        if hasattr(t, "children") and t.children:
            result.extend(_flatten_tasks(t.children, depth + 1, exclude_id))
    return result


async def _get_all_tasks_tree(db: AsyncSession, project_id: int) -> list[Task]:
    """Get all tasks in project as a tree (top-level with children loaded)."""
    stmt = (
        select(Task)
        .options(selectinload(Task.children).selectinload(Task.children))
        .where(Task.project_id == project_id, Task.parent_id.is_(None))
        .order_by(Task.priority.asc())
    )
    return list((await db.scalars(stmt)).all())


@router.get("/projects/{project_id}/tasks/new", response_class=HTMLResponse)
async def new_task_page(
    request: Request,
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    tree = await _get_all_tasks_tree(db, project_id)
    tasks_data = _flatten_tasks(tree)

    project_data = {
        "id": project.id,
        "name": project.name,
    }

    return templates.TemplateResponse(request, "task_form.html", {
        "project": project_data,
        "tasks": tasks_data,
        "task": None,
        "is_edit": False,
    })


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
async def edit_task_page(
    request: Request,
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(db, task_id)
    project = await db.get(Project, task.project_id)

    tree = await _get_all_tasks_tree(db, task.project_id)
    tasks_data = _flatten_tasks(tree, exclude_id=task.id)

    task_data = {
        "id": task.id,
        "project_id": task.project_id,
        "parent_id": task.parent_id,
        "title": task.title,
        "description": task.description or "",
        "start_time": task.start_time.strftime("%Y-%m-%dT%H:%M") if task.start_time else "",
        "end_time": task.end_time.strftime("%Y-%m-%dT%H:%M") if task.end_time else "",
        "assigned_member": task.assigned_member or "",
        "priority": task.priority,
        "is_completed": task.is_completed,
    }

    project_data = {
        "id": project.id,
        "name": project.name,
    }

    return templates.TemplateResponse(request, "task_form.html", {
        "project": project_data,
        "tasks": tasks_data,
        "task": task_data,
        "is_edit": True,
    })


@router.get("/projects/new", response_class=HTMLResponse)
async def new_project_page(request: Request):
    return templates.TemplateResponse(request, "project_form.html", {
        "project": None,
        "is_edit": False,
    })


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_page(
    request: Request,
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "start_date": str(project.start_date) if project.start_date else "",
        "end_date": str(project.end_date) if project.end_date else "",
        "team_members": ", ".join(project.team_members) if project.team_members else "",
    }

    return templates.TemplateResponse(request, "project_form.html", {
        "project": project_data,
        "is_edit": True,
    })
