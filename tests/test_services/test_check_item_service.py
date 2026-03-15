import pytest
from app.models.project import Project
from app.models.task import Task
from app.schemas.check_item import CheckItemCreate, CheckItemUpdate
from app.services import check_item_service
from app.exceptions import NotFoundError


async def _make_task(db):
    project = Project(name="P")
    db.add(project)
    await db.commit()
    await db.refresh(project)
    task = Task(project_id=project.id, title="Task")
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def test_create_check_item(db):
    task = await _make_task(db)
    data = CheckItemCreate(
        title="Check 1",
        inputs=["input1"],
        outputs=["output1"],
    )
    item = await check_item_service.create_check_item(db, task.id, data)

    assert item.id is not None
    assert item.title == "Check 1"
    assert item.inputs == ["input1"]
    assert item.outputs == ["output1"]
    assert item.is_checked is False


async def test_create_check_item_task_not_found(db):
    data = CheckItemCreate(title="Check")
    with pytest.raises(NotFoundError):
        await check_item_service.create_check_item(db, 9999, data)


async def test_get_check_items_by_task(db):
    task = await _make_task(db)
    await check_item_service.create_check_item(db, task.id, CheckItemCreate(title="A"))
    await check_item_service.create_check_item(db, task.id, CheckItemCreate(title="B"))

    items = await check_item_service.get_check_items_by_task(db, task.id)
    assert len(items) == 2


async def test_get_check_items_by_task_not_found(db):
    with pytest.raises(NotFoundError):
        await check_item_service.get_check_items_by_task(db, 9999)


async def test_get_check_item(db):
    task = await _make_task(db)
    created = await check_item_service.create_check_item(
        db, task.id, CheckItemCreate(title="Get me")
    )
    fetched = await check_item_service.get_check_item(db, created.id)
    assert fetched.title == "Get me"


async def test_get_check_item_not_found(db):
    with pytest.raises(NotFoundError):
        await check_item_service.get_check_item(db, 9999)


async def test_update_check_item(db):
    task = await _make_task(db)
    created = await check_item_service.create_check_item(
        db, task.id, CheckItemCreate(title="Old")
    )
    updated = await check_item_service.update_check_item(
        db, created.id, CheckItemUpdate(title="New")
    )
    assert updated.title == "New"


async def test_update_check_item_checked_at_auto_set(db):
    task = await _make_task(db)
    created = await check_item_service.create_check_item(
        db, task.id, CheckItemCreate(title="Check")
    )
    assert created.checked_at is None

    # Check it
    updated = await check_item_service.update_check_item(
        db, created.id, CheckItemUpdate(is_checked=True)
    )
    assert updated.is_checked is True
    assert updated.checked_at is not None

    # Uncheck it
    unchecked = await check_item_service.update_check_item(
        db, created.id, CheckItemUpdate(is_checked=False)
    )
    assert unchecked.is_checked is False
    assert unchecked.checked_at is None


async def test_update_check_item_not_found(db):
    with pytest.raises(NotFoundError):
        await check_item_service.update_check_item(
            db, 9999, CheckItemUpdate(title="x")
        )


async def test_delete_check_item(db):
    task = await _make_task(db)
    created = await check_item_service.create_check_item(
        db, task.id, CheckItemCreate(title="Del")
    )
    await check_item_service.delete_check_item(db, created.id)

    with pytest.raises(NotFoundError):
        await check_item_service.get_check_item(db, created.id)


async def test_delete_check_item_not_found(db):
    with pytest.raises(NotFoundError):
        await check_item_service.delete_check_item(db, 9999)
