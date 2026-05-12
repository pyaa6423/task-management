from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from datetime import date
from app.database import get_db
from app.exceptions import NotFoundError
from app.models.project import Project
from app.models.task import Task
from app.services import deliverable_service

router = APIRouter(tags=["project_status"])
templates = Jinja2Templates(directory="app/templates")


STATUS_LABELS = {
    "not_started": "未着手",
    "in_progress": "進行中",
    "done": "完了",
}


def _deliverable_to_dict(d, task_stats: dict[int, dict]) -> dict:
    stat = task_stats.get(d.id, {"total": 0, "done": 0})
    progress = round(stat["done"] / stat["total"] * 100) if stat["total"] > 0 else None
    return {
        "id": d.id,
        "title": d.title,
        "purpose": d.purpose,
        "value": d.value,
        "next_action": d.next_action,
        "target_date": d.target_date.isoformat() if d.target_date else None,
        "target_date_display": d.target_date.strftime("%Y/%m/%d") if d.target_date else None,
        "status": d.status,
        "status_label": STATUS_LABELS.get(d.status, d.status),
        "task_total": stat["total"],
        "task_done": stat["done"],
        "progress": progress,
        "is_overdue": (
            d.target_date is not None
            and d.target_date < date.today()
            and d.status != "done"
        ),
    }


async def _task_stats(db: AsyncSession, project_id: int) -> dict[int, dict]:
    """Aggregate task counts per deliverable_id."""
    stmt = (
        select(
            Task.deliverable_id,
            func.count(Task.id).label("total"),
            func.sum(case((Task.is_completed.is_(True), 1), else_=0)).label("done"),
        )
        .where(Task.project_id == project_id, Task.deliverable_id.is_not(None))
        .group_by(Task.deliverable_id)
    )
    rows = (await db.execute(stmt)).all()
    return {r.deliverable_id: {"total": r.total or 0, "done": int(r.done or 0)} for r in rows}


@router.get("/projects/status", response_class=HTMLResponse)
async def project_status_index(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    projects = list(
        (await db.scalars(
            select(Project).order_by(Project.is_completed.asc(), Project.created_at.desc())
        )).all()
    )
    if not projects:
        return templates.TemplateResponse(request, "project_status.html", {
            "project": None,
            "projects": [],
            "deliverables": [],
            "summary": None,
        })
    return RedirectResponse(url=f"/projects/{projects[0].id}/status")


@router.get("/projects/{project_id}/status", response_class=HTMLResponse)
async def project_status_page(
    request: Request,
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    projects = list(
        (await db.scalars(
            select(Project).order_by(Project.is_completed.asc(), Project.created_at.desc())
        )).all()
    )

    top_deliverables = await deliverable_service.get_by_project(db, project_id)
    task_stats = await _task_stats(db, project_id)

    deliverables_data = []
    summary = {"total": 0, "done": 0, "in_progress": 0, "not_started": 0, "overdue": 0}
    for d in top_deliverables:
        parent_data = _deliverable_to_dict(d, task_stats)
        parent_data["children"] = [
            _deliverable_to_dict(c, task_stats) for c in (d.children or [])
        ]
        deliverables_data.append(parent_data)
        # Summary counts all deliverables (parent + children)
        for x in [parent_data] + parent_data["children"]:
            summary["total"] += 1
            summary[x["status"]] = summary.get(x["status"], 0) + 1
            if x["is_overdue"]:
                summary["overdue"] += 1

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "start_date": project.start_date.strftime("%Y/%m/%d") if project.start_date else None,
        "end_date": project.end_date.strftime("%Y/%m/%d") if project.end_date else None,
        "team_members": project.team_members or [],
        "color": project.color or "#e60012",
        "is_completed": project.is_completed,
    }

    return templates.TemplateResponse(request, "project_status.html", {
        "project": project_data,
        "projects": [{"id": p.id, "name": p.name, "selected": p.id == project_id} for p in projects],
        "deliverables": deliverables_data,
        "summary": summary,
    })
