import pytest
from datetime import date
from app.models.project import Project
from app.services import event_service
from app.schemas.event import EventCreate, EventUpdate
from app.exceptions import NotFoundError


async def _make_project(db, name="TestProj"):
    project = Project(name=name)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def test_create_event(db):
    data = EventCreate(title="Launch", event_date=date(2026, 4, 1))
    event = await event_service.create_event(db, data)
    assert event.id is not None
    assert event.title == "Launch"
    assert event.event_date == date(2026, 4, 1)
    assert event.project_id is None
    assert event.color == "#e60012"


async def test_create_event_with_project(db):
    project = await _make_project(db)
    data = EventCreate(title="Sprint", event_date=date(2026, 5, 1), project_id=project.id)
    event = await event_service.create_event(db, data)
    assert event.project_id == project.id


async def test_create_event_project_not_found(db):
    data = EventCreate(title="X", event_date=date(2026, 1, 1), project_id=9999)
    with pytest.raises(NotFoundError):
        await event_service.create_event(db, data)


async def test_get_event(db):
    data = EventCreate(title="Get Me", event_date=date(2026, 3, 15))
    created = await event_service.create_event(db, data)
    fetched = await event_service.get_event(db, created.id)
    assert fetched.title == "Get Me"


async def test_get_event_not_found(db):
    with pytest.raises(NotFoundError):
        await event_service.get_event(db, 9999)


async def test_get_events_all(db):
    await event_service.create_event(db, EventCreate(title="A", event_date=date(2026, 1, 1)))
    await event_service.create_event(db, EventCreate(title="B", event_date=date(2026, 2, 1)))
    events = await event_service.get_events(db)
    assert len(events) >= 2


async def test_get_events_filter_by_project(db):
    project = await _make_project(db, "FilterProj")
    await event_service.create_event(db, EventCreate(
        title="ProjEvent", event_date=date(2026, 3, 1), project_id=project.id
    ))
    await event_service.create_event(db, EventCreate(
        title="GlobalEvent", event_date=date(2026, 3, 2)
    ))
    project2 = await _make_project(db, "OtherProj")
    await event_service.create_event(db, EventCreate(
        title="OtherEvent", event_date=date(2026, 3, 3), project_id=project2.id
    ))

    events = await event_service.get_events(db, project_id=project.id)
    titles = {e.title for e in events}
    assert "ProjEvent" in titles
    assert "GlobalEvent" in titles
    assert "OtherEvent" not in titles


async def test_update_event(db):
    created = await event_service.create_event(db, EventCreate(
        title="Old", event_date=date(2026, 6, 1)
    ))
    updated = await event_service.update_event(db, created.id, EventUpdate(title="New"))
    assert updated.title == "New"
    assert updated.event_date == date(2026, 6, 1)


async def test_update_event_not_found(db):
    with pytest.raises(NotFoundError):
        await event_service.update_event(db, 9999, EventUpdate(title="X"))


async def test_delete_event(db):
    created = await event_service.create_event(db, EventCreate(
        title="ToDelete", event_date=date(2026, 7, 1)
    ))
    await event_service.delete_event(db, created.id)
    with pytest.raises(NotFoundError):
        await event_service.get_event(db, created.id)


async def test_delete_event_not_found(db):
    with pytest.raises(NotFoundError):
        await event_service.delete_event(db, 9999)
