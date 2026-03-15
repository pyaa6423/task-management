import pytest
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.schemas.subtask import SubTaskCreate, SubTaskUpdate
from app.services import project_service, task_service, subtask_service
from app.exceptions import NotFoundError


async def _make_task(db):
    project = await project_service.create_project(db, ProjectCreate(name="P"))
    return await task_service.create_task(db, project.id, TaskCreate(title="T"))


async def test_create_subtask(db):
    task = await _make_task(db)
    data = SubTaskCreate(title="Sub 1", priority=1)
    subtask = await subtask_service.create_subtask(db, task.id, data)

    assert subtask.id is not None
    assert subtask.title == "Sub 1"
    assert subtask.task_id == task.id


async def test_create_subtask_task_not_found(db):
    with pytest.raises(NotFoundError):
        await subtask_service.create_subtask(db, 9999, SubTaskCreate(title="X"))


async def test_get_subtask(db):
    task = await _make_task(db)
    created = await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="S"))
    fetched = await subtask_service.get_subtask(db, created.id)
    assert fetched.title == "S"


async def test_get_subtask_not_found(db):
    with pytest.raises(NotFoundError):
        await subtask_service.get_subtask(db, 9999)


async def test_list_subtasks_by_task(db):
    task = await _make_task(db)
    await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="S1", priority=2))
    await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="S2", priority=1))
    subtasks = await subtask_service.get_subtasks_by_task(db, task.id)

    assert len(subtasks) == 2
    assert subtasks[0].title == "S2"  # priority 1 first


async def test_update_subtask(db):
    task = await _make_task(db)
    sub = await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="Old"))
    updated = await subtask_service.update_subtask(db, sub.id, SubTaskUpdate(title="New"))
    assert updated.title == "New"


async def test_complete_subtask(db):
    task = await _make_task(db)
    sub = await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="S"))
    updated = await subtask_service.update_subtask(db, sub.id, SubTaskUpdate(is_completed=True))
    assert updated.is_completed is True
    assert updated.completed_at is not None


async def test_uncomplete_subtask(db):
    task = await _make_task(db)
    sub = await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="S"))
    await subtask_service.update_subtask(db, sub.id, SubTaskUpdate(is_completed=True))
    updated = await subtask_service.update_subtask(db, sub.id, SubTaskUpdate(is_completed=False))
    assert updated.is_completed is False
    assert updated.completed_at is None


async def test_delete_subtask(db):
    task = await _make_task(db)
    sub = await subtask_service.create_subtask(db, task.id, SubTaskCreate(title="Del"))
    await subtask_service.delete_subtask(db, sub.id)

    with pytest.raises(NotFoundError):
        await subtask_service.get_subtask(db, sub.id)
