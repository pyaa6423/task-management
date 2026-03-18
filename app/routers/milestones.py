from __future__ import annotations
from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.database import get_db
from app.models.task import Task
from app.models.project import Project

if TYPE_CHECKING:
    from app.models.check_item import CheckItem

router = APIRouter(tags=["milestones"])
templates = Jinja2Templates(directory="app/templates")


def _check_item_to_dict(ci: "CheckItem") -> dict:
    return {
        "id": ci.id,
        "title": ci.title,
        "is_checked": ci.is_checked,
        "checked_at": ci.checked_at.isoformat() if ci.checked_at else None,
        "inputs": ci.inputs or [],
        "outputs": ci.outputs or [],
        "results": ci.results or [],
        "evidences": ci.evidences or [],
    }


def _task_to_dict(task: Task) -> dict:
    from datetime import datetime
    children = sorted(
        (task.children or []),
        key=lambda t: (t.start_time or datetime.max),
    )
    return {
        "id": task.id,
        "title": task.title,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "assigned_member": task.assigned_member,
        "is_completed": task.is_completed,
        "priority": task.priority,
        "children": [_task_to_dict(c) for c in children],
        "check_items": [_check_item_to_dict(ci) for ci in (task.check_items or [])],
    }


@router.get("/milestones", response_class=HTMLResponse)
async def milestones_page(request: Request, db: AsyncSession = Depends(get_db)):
    projects = (await db.scalars(select(Project).order_by(Project.start_date.asc()))).all()
    return templates.TemplateResponse(request, "milestones.html", {"projects": projects})


@router.get("/api/v1/milestones")
async def milestones_api(db: AsyncSession = Depends(get_db)):
    projects = (await db.scalars(
        select(Project).order_by(Project.start_date.asc())
    )).all()

    result = []
    for project in projects:
        stmt = (
            select(Task)
            .options(
                selectinload(Task.children).selectinload(Task.children),
                selectinload(Task.children).selectinload(Task.check_items),
                selectinload(Task.check_items),
            )
            .where(Task.project_id == project.id, Task.parent_id.is_(None))
            .order_by(Task.start_time.asc())
        )
        tasks = (await db.scalars(stmt)).all()
        result.append({
            "id": project.id,
            "name": project.name,
            "start_date": str(project.start_date) if project.start_date else None,
            "end_date": str(project.end_date) if project.end_date else None,
            "tasks": [_task_to_dict(t) for t in tasks],
        })
    return result
