from datetime import date as Date
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.daily import (
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryResponse,
    DailyNoteUpsert,
    DailyNoteResponse,
    DailyTaskCreate,
    DailyTaskResponse,
)
from app.services import daily_service
from app.models.project import Project

router = APIRouter(tags=["daily"])
templates = Jinja2Templates(directory="app/templates")


# ---- HTML page ----

@router.get("/daily", response_class=HTMLResponse)
async def daily_page(
    request: Request,
    d: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    target = Date.fromisoformat(d) if d else Date.today()
    projects = (await db.scalars(select(Project).order_by(Project.name.asc()))).all()
    return templates.TemplateResponse(request, "daily.html", {
        "target_date": target.isoformat(),
        "projects": projects,
    })


# ---- DailyNote API ----

@router.get("/api/v1/daily/notes/{note_date}", response_model=DailyNoteResponse)
async def get_note(note_date: Date, db: AsyncSession = Depends(get_db)):
    return await daily_service.get_note(db, note_date)


@router.put("/api/v1/daily/notes/{note_date}", response_model=DailyNoteResponse)
async def upsert_note(
    note_date: Date,
    data: DailyNoteUpsert,
    db: AsyncSession = Depends(get_db),
):
    return await daily_service.upsert_note(db, note_date, data)


# ---- TimeEntry API ----

@router.get("/api/v1/daily/entries", response_model=list[TimeEntryResponse])
async def list_entries(
    entry_date: Date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await daily_service.list_entries(db, entry_date=entry_date)


@router.post("/api/v1/daily/entries", response_model=TimeEntryResponse, status_code=201)
async def create_entry(
    data: TimeEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    return await daily_service.create_entry(db, data)


@router.get("/api/v1/daily/entries/{entry_id}", response_model=TimeEntryResponse)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    return await daily_service.get_entry(db, entry_id)


@router.put("/api/v1/daily/entries/{entry_id}", response_model=TimeEntryResponse)
async def update_entry(
    entry_id: int,
    data: TimeEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await daily_service.update_entry(db, entry_id, data)


@router.delete("/api/v1/daily/entries/{entry_id}", status_code=204)
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    await daily_service.delete_entry(db, entry_id)


# ---- DailyTask API (today's task list) ----

@router.get("/api/v1/daily/tasks", response_model=list[DailyTaskResponse])
async def list_daily_tasks(
    daily_date: Date = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    return await daily_service.list_daily_tasks(db, daily_date=daily_date)


@router.post("/api/v1/daily/tasks", response_model=DailyTaskResponse, status_code=201)
async def add_daily_task(
    data: DailyTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    return await daily_service.add_daily_task(db, data)


@router.delete("/api/v1/daily/tasks/{daily_task_id}", status_code=204)
async def remove_daily_task(daily_task_id: int, db: AsyncSession = Depends(get_db)):
    await daily_service.remove_daily_task(db, daily_task_id)
