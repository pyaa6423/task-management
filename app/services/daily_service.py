from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.time_entry import TimeEntry
from app.models.daily_note import DailyNote
from app.models.project import Project
from app.models.task import Task
from app.schemas.daily import TimeEntryCreate, TimeEntryUpdate, DailyNoteUpsert
from app.exceptions import NotFoundError, ValidationError


# ---- TimeEntry ----

async def list_entries(
    db: AsyncSession,
    entry_date: date | None = None,
) -> list[TimeEntry]:
    stmt = select(TimeEntry).order_by(TimeEntry.start_at.asc())
    if entry_date is not None:
        stmt = stmt.where(TimeEntry.entry_date == entry_date)
    return list((await db.scalars(stmt)).all())


async def get_entry(db: AsyncSession, entry_id: int) -> TimeEntry:
    entry = await db.get(TimeEntry, entry_id)
    if not entry:
        raise NotFoundError("TimeEntry", entry_id)
    return entry


async def _validate_refs(db: AsyncSession, project_id: int | None, task_id: int | None) -> None:
    if project_id is not None:
        if not await db.get(Project, project_id):
            raise NotFoundError("Project", project_id)
    if task_id is not None:
        if not await db.get(Task, task_id):
            raise NotFoundError("Task", task_id)


def _validate_range(start_at, end_at) -> None:
    if start_at and end_at and end_at <= start_at:
        raise ValidationError("end_at must be after start_at")


async def create_entry(db: AsyncSession, data: TimeEntryCreate) -> TimeEntry:
    _validate_range(data.start_at, data.end_at)
    await _validate_refs(db, data.project_id, data.task_id)
    entry = TimeEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def update_entry(db: AsyncSession, entry_id: int, data: TimeEntryUpdate) -> TimeEntry:
    entry = await get_entry(db, entry_id)
    update_data = data.model_dump(exclude_unset=True)
    new_start = update_data.get("start_at", entry.start_at)
    new_end = update_data.get("end_at", entry.end_at)
    _validate_range(new_start, new_end)
    await _validate_refs(
        db,
        update_data.get("project_id") if "project_id" in update_data else None,
        update_data.get("task_id") if "task_id" in update_data else None,
    )
    for key, value in update_data.items():
        setattr(entry, key, value)
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete_entry(db: AsyncSession, entry_id: int) -> None:
    entry = await get_entry(db, entry_id)
    await db.delete(entry)
    await db.commit()


# ---- DailyNote ----

async def get_note(db: AsyncSession, note_date: date) -> DailyNote:
    note = await db.get(DailyNote, note_date)
    if not note:
        # Return an empty placeholder (not persisted) so GET always succeeds
        return DailyNote(note_date=note_date, body="")
    return note


async def upsert_note(db: AsyncSession, note_date: date, data: DailyNoteUpsert) -> DailyNote:
    note = await db.get(DailyNote, note_date)
    if note:
        note.body = data.body
    else:
        note = DailyNote(note_date=note_date, body=data.body)
        db.add(note)
    await db.commit()
    await db.refresh(note)
    return note
