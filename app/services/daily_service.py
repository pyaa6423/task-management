from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.time_entry import TimeEntry
from app.models.daily_note import DailyNote
from app.models.daily_task import DailyTask
from app.models.project import Project
from app.models.task import Task
from app.schemas.daily import TimeEntryCreate, TimeEntryUpdate, DailyNoteUpsert, DailyTaskCreate
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


# ---- DailyTask (today's tasks list, links to existing Task) ----

def _serialize_daily_task(dt: DailyTask, t: Task, p: Project) -> dict:
    return {
        "id": dt.id,
        "daily_date": dt.daily_date,
        "task_id": dt.task_id,
        "position": dt.position,
        "created_at": dt.created_at,
        "task_title": t.title,
        "task_is_completed": t.is_completed,
        "task_assigned_member": t.assigned_member,
        "project_id": p.id,
        "project_name": p.name,
    }


async def list_daily_tasks(db: AsyncSession, daily_date: date) -> list[dict]:
    stmt = (
        select(DailyTask, Task, Project)
        .join(Task, DailyTask.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(DailyTask.daily_date == daily_date)
        .order_by(DailyTask.position.asc(), DailyTask.id.asc())
    )
    rows = (await db.execute(stmt)).all()
    return [_serialize_daily_task(dt, t, p) for dt, t, p in rows]


async def add_daily_task(db: AsyncSession, data: DailyTaskCreate) -> dict:
    task = await db.get(Task, data.task_id)
    if not task:
        raise NotFoundError("Task", data.task_id)
    project = await db.get(Project, task.project_id)

    # If already linked for the date, return the existing one (idempotent add)
    existing = await db.scalar(
        select(DailyTask).where(
            DailyTask.daily_date == data.daily_date,
            DailyTask.task_id == data.task_id,
        )
    )
    if existing:
        return _serialize_daily_task(existing, task, project)

    # Compute next position
    max_pos = await db.scalar(
        select(DailyTask.position)
        .where(DailyTask.daily_date == data.daily_date)
        .order_by(DailyTask.position.desc())
        .limit(1)
    )
    dt = DailyTask(
        daily_date=data.daily_date,
        task_id=data.task_id,
        position=(max_pos or 0) + 1,
    )
    db.add(dt)
    await db.commit()
    await db.refresh(dt)
    return _serialize_daily_task(dt, task, project)


async def remove_daily_task(db: AsyncSession, daily_task_id: int) -> None:
    dt = await db.get(DailyTask, daily_task_id)
    if not dt:
        raise NotFoundError("DailyTask", daily_task_id)
    await db.delete(dt)
    await db.commit()
