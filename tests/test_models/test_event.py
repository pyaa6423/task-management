from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.event import Event


async def test_create_event(db):
    event = Event(title="Release Day", event_date=date(2026, 4, 1))
    db.add(event)
    await db.commit()
    await db.refresh(event)

    assert event.id is not None
    assert event.title == "Release Day"
    assert event.event_date == date(2026, 4, 1)
    assert event.project_id is None
    assert event.color == "#e60012"


async def test_create_event_with_project(db):
    project = Project(name="TestProject")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    event = Event(
        title="Sprint End",
        event_date=date(2026, 5, 15),
        project_id=project.id,
        color="#0068b7",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    assert event.project_id == project.id
    assert event.color == "#0068b7"


async def test_event_project_relationship(db):
    project = Project(name="RelProject")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    ev1 = Event(title="Ev1", event_date=date(2026, 3, 1), project_id=project.id)
    ev2 = Event(title="Ev2", event_date=date(2026, 3, 10), project_id=project.id)
    db.add_all([ev1, ev2])
    await db.commit()

    stmt = select(Project).options(selectinload(Project.events)).where(Project.id == project.id)
    p = await db.scalar(stmt)
    assert len(p.events) == 2
    assert {e.title for e in p.events} == {"Ev1", "Ev2"}


async def test_event_cascade_delete(db):
    project = Project(name="CascadeProject")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    event = Event(title="WillBeDeleted", event_date=date(2026, 6, 1), project_id=project.id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    event_id = event.id

    await db.delete(project)
    await db.commit()

    result = await db.get(Event, event_id)
    assert result is None


async def test_event_global_no_project(db):
    event = Event(title="Global Event", event_date=date(2026, 1, 1), description="New Year")
    db.add(event)
    await db.commit()
    await db.refresh(event)

    assert event.project_id is None
    assert event.description == "New Year"
