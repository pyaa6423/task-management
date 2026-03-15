from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import task_service
from app.models.project import Project

router = APIRouter(tags=["task_pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/projects/{project_id}/tasks/new", response_class=HTMLResponse)
async def new_task_page(
    request: Request,
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        from app.exceptions import NotFoundError
        raise NotFoundError("Project", project_id)

    # Load top-level tasks for parent select dropdown
    tasks = await task_service.get_tasks_by_project(db, project_id)
    tasks_data = [
        {
            "id": t.id,
            "title": t.title,
        }
        for t in tasks
    ]

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

    # Load top-level tasks for parent select dropdown (exclude self)
    all_tasks = await task_service.get_tasks_by_project(db, task.project_id)
    tasks_data = [
        {
            "id": t.id,
            "title": t.title,
        }
        for t in all_tasks
        if t.id != task.id
    ]

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
