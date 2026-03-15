from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.database import get_db
from app.models.task import Task
from app.models.subtask import SubTask
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
        .options(selectinload(Task.subtasks))
        .where(Task.project_id == project_id)
        .order_by(Task.priority.asc())
    )
    tasks = (await db.scalars(stmt)).all()

    result = []
    for task in tasks:
        completed_subtasks = sum(1 for s in task.subtasks if s.is_completed)
        total_subtasks = len(task.subtasks)
        progress = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0

        result.append({
            "id": f"task-{task.id}",
            "name": task.title,
            "start": task.start_time.isoformat() if task.start_time else None,
            "end": task.end_time.isoformat() if task.end_time else None,
            "progress": progress,
            "priority": task.priority,
            "is_completed": task.is_completed,
            "has_children": total_subtasks > 0,
        })
    return result


@router.get("/api/v1/gantt/tasks/{task_id}/subtasks")
async def gantt_task_subtasks(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SubTask)
        .where(SubTask.task_id == task_id)
        .order_by(SubTask.priority.asc())
    )
    subtasks = (await db.scalars(stmt)).all()

    return [
        {
            "id": f"subtask-{s.id}",
            "name": s.title,
            "start": s.start_time.isoformat() if s.start_time else None,
            "end": s.end_time.isoformat() if s.end_time else None,
            "progress": 100 if s.is_completed else 0,
            "priority": s.priority,
            "is_completed": s.is_completed,
            "has_children": False,
        }
        for s in subtasks
    ]
