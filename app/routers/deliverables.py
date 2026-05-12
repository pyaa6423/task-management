from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.exceptions import NotFoundError
from app.schemas.deliverable import (
    DeliverableCreate,
    DeliverableUpdate,
    DeliverableResponse,
)
from app.services import deliverable_service
from app.models.project import Project
from app.models.deliverable import Deliverable

router = APIRouter(tags=["deliverables"])
templates = Jinja2Templates(directory="app/templates")


# ---- API ----
@router.get(
    "/api/v1/projects/{project_id}/deliverables",
    response_model=list[DeliverableResponse],
)
async def list_deliverables(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await deliverable_service.get_by_project(db, project_id)


@router.post(
    "/api/v1/projects/{project_id}/deliverables",
    response_model=DeliverableResponse,
    status_code=201,
)
async def create_deliverable(
    project_id: int,
    data: DeliverableCreate,
    db: AsyncSession = Depends(get_db),
):
    return await deliverable_service.create_deliverable(db, project_id, data)


@router.get("/api/v1/deliverables/{deliverable_id}", response_model=DeliverableResponse)
async def get_deliverable(
    deliverable_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await deliverable_service.get_deliverable(db, deliverable_id)


@router.put("/api/v1/deliverables/{deliverable_id}", response_model=DeliverableResponse)
async def update_deliverable(
    deliverable_id: int,
    data: DeliverableUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await deliverable_service.update_deliverable(db, deliverable_id, data)


@router.delete("/api/v1/deliverables/{deliverable_id}", status_code=204)
async def delete_deliverable(
    deliverable_id: int,
    db: AsyncSession = Depends(get_db),
):
    await deliverable_service.delete_deliverable(db, deliverable_id)


# ---- Form pages ----
def _project_options(projects: list[Project], current_id: int) -> list[dict]:
    return [{"id": p.id, "name": p.name, "selected": p.id == current_id} for p in projects]


async def _parent_options(db: AsyncSession, project_id: int, exclude_id: int | None) -> list[dict]:
    """Top-level deliverables only (since nesting is 2 levels)."""
    stmt = (
        select(Deliverable)
        .where(Deliverable.project_id == project_id, Deliverable.parent_id.is_(None))
        .order_by(Deliverable.sort_order.asc(), Deliverable.created_at.asc())
    )
    rows = list((await db.scalars(stmt)).all())
    return [{"id": d.id, "title": d.title} for d in rows if d.id != exclude_id]


@router.get("/projects/{project_id}/deliverables/new", response_class=HTMLResponse)
async def new_deliverable_page(
    request: Request,
    project_id: int,
    parent_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)

    parents = await _parent_options(db, project_id, exclude_id=None)
    return templates.TemplateResponse(request, "deliverable_form.html", {
        "project": {"id": project.id, "name": project.name},
        "deliverable": None,
        "is_edit": False,
        "parents": parents,
        "initial_parent_id": parent_id,
    })


@router.get("/deliverables/{deliverable_id}/edit", response_class=HTMLResponse)
async def edit_deliverable_page(
    request: Request,
    deliverable_id: int,
    db: AsyncSession = Depends(get_db),
):
    d = await deliverable_service.get_deliverable(db, deliverable_id)
    project = await db.get(Project, d.project_id)
    parents = await _parent_options(db, d.project_id, exclude_id=d.id)

    deliverable_data = {
        "id": d.id,
        "project_id": d.project_id,
        "parent_id": d.parent_id,
        "title": d.title,
        "purpose": d.purpose or "",
        "value": d.value or "",
        "next_action": d.next_action or "",
        "target_date": str(d.target_date) if d.target_date else "",
        "status": d.status,
        "sort_order": d.sort_order,
        "has_children": bool(d.children),
    }
    return templates.TemplateResponse(request, "deliverable_form.html", {
        "project": {"id": project.id, "name": project.name},
        "deliverable": deliverable_data,
        "is_edit": True,
        "parents": parents,
        "initial_parent_id": d.parent_id,
    })
