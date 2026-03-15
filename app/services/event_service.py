from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.models.project import Project
from app.schemas.event import EventCreate, EventUpdate
from app.exceptions import NotFoundError


async def get_events(db: AsyncSession, project_id: int | None = None) -> list[Event]:
    if project_id is not None:
        # Return events for this project + global events (project_id is None)
        stmt = (
            select(Event)
            .where(or_(Event.project_id == project_id, Event.project_id.is_(None)))
            .order_by(Event.event_date.asc())
        )
    else:
        stmt = select(Event).order_by(Event.event_date.asc())
    return list((await db.scalars(stmt)).all())


async def get_event(db: AsyncSession, event_id: int) -> Event:
    event = await db.get(Event, event_id)
    if not event:
        raise NotFoundError("Event", event_id)
    return event


async def create_event(db: AsyncSession, data: EventCreate) -> Event:
    if data.project_id is not None:
        project = await db.get(Project, data.project_id)
        if not project:
            raise NotFoundError("Project", data.project_id)

    event = Event(**data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def update_event(db: AsyncSession, event_id: int, data: EventUpdate) -> Event:
    event = await get_event(db, event_id)
    update_data = data.model_dump(exclude_unset=True)

    if "project_id" in update_data and update_data["project_id"] is not None:
        project = await db.get(Project, update_data["project_id"])
        if not project:
            raise NotFoundError("Project", update_data["project_id"])

    for key, value in update_data.items():
        setattr(event, key, value)

    await db.commit()
    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event_id: int) -> None:
    event = await get_event(db, event_id)
    await db.delete(event)
    await db.commit()
