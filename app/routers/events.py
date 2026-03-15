from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.event import EventCreate, EventUpdate, EventResponse
from app.services import event_service
from app.models.project import Project

router = APIRouter(tags=["events"])
templates = Jinja2Templates(directory="app/templates")


# HTML page
@router.get("/events", response_class=HTMLResponse)
async def events_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    projects = (await db.scalars(select(Project).order_by(Project.name.asc()))).all()
    events = await event_service.get_events(db)
    # Serialize events for template
    events_data = []
    project_map = {p.id: p.name for p in projects}
    for ev in events:
        events_data.append({
            "id": ev.id,
            "title": ev.title,
            "description": ev.description,
            "event_date": str(ev.event_date),
            "project_id": ev.project_id,
            "project_name": project_map.get(ev.project_id, "全体") if ev.project_id else "全体",
            "color": ev.color or "#e60012",
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
            "updated_at": ev.updated_at.isoformat() if ev.updated_at else None,
        })
    return templates.TemplateResponse(request, "events.html", {
        "projects": projects,
        "events": events_data,
    })


# API endpoints
@router.get("/api/v1/events", response_model=list[EventResponse])
async def list_events(
    project_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await event_service.get_events(db, project_id=project_id)


@router.post("/api/v1/events", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    return await event_service.create_event(db, data)


@router.get("/api/v1/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await event_service.get_event(db, event_id)


@router.put("/api/v1/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await event_service.update_event(db, event_id, data)


@router.delete("/api/v1/events/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    await event_service.delete_event(db, event_id)
