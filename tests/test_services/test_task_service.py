import pytest
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import project_service, task_service
from app.exceptions import NotFoundError, ConflictError


async def _make_project(db):
    return await project_service.create_project(db, ProjectCreate(name="P"))


async def test_create_task(db):
    project = await _make_project(db)
    data = TaskCreate(title="New Task", priority=1)
    task = await task_service.create_task(db, project.id, data)

    assert task.id is not None
    assert task.title == "New Task"
    assert task.project_id == project.id
    assert task.parent_id is None


async def test_create_task_project_not_found(db):
    with pytest.raises(NotFoundError):
        await task_service.create_task(db, 9999, TaskCreate(title="X"))


async def test_create_child_task(db):
    project = await _make_project(db)
    parent = await task_service.create_task(db, project.id, TaskCreate(title="Parent"))
    child = await task_service.create_task(db, project.id, TaskCreate(title="Child"), parent_id=parent.id)

    assert child.parent_id == parent.id
    assert child.project_id == project.id


async def test_create_child_task_parent_not_found(db):
    project = await _make_project(db)
    with pytest.raises(NotFoundError):
        await task_service.create_task(db, project.id, TaskCreate(title="X"), parent_id=9999)


async def test_get_task(db):
    project = await _make_project(db)
    created = await task_service.create_task(db, project.id, TaskCreate(title="T"))
    fetched = await task_service.get_task(db, created.id)
    assert fetched.title == "T"


async def test_get_task_not_found(db):
    with pytest.raises(NotFoundError):
        await task_service.get_task(db, 9999)


async def test_list_tasks_by_project(db):
    project = await _make_project(db)
    await task_service.create_task(db, project.id, TaskCreate(title="T1", priority=2))
    await task_service.create_task(db, project.id, TaskCreate(title="T2", priority=1))
    tasks = await task_service.get_tasks_by_project(db, project.id)

    assert len(tasks) == 2
    assert tasks[0].title == "T2"  # priority 1 first


async def test_list_tasks_excludes_children(db):
    project = await _make_project(db)
    parent = await task_service.create_task(db, project.id, TaskCreate(title="Parent"))
    await task_service.create_task(db, project.id, TaskCreate(title="Child"), parent_id=parent.id)
    tasks = await task_service.get_tasks_by_project(db, project.id)

    assert len(tasks) == 1
    assert tasks[0].title == "Parent"


async def test_update_task(db):
    project = await _make_project(db)
    task = await task_service.create_task(db, project.id, TaskCreate(title="Old"))
    updated = await task_service.update_task(db, task.id, TaskUpdate(title="New"))
    assert updated.title == "New"


async def test_complete_task_with_incomplete_children(db):
    project = await _make_project(db)
    parent = await task_service.create_task(db, project.id, TaskCreate(title="Parent"))
    await task_service.create_task(db, project.id, TaskCreate(title="Incomplete child"), parent_id=parent.id)

    with pytest.raises(ConflictError):
        await task_service.update_task(db, parent.id, TaskUpdate(is_completed=True))


async def test_complete_task_all_children_done(db):
    project = await _make_project(db)
    parent = await task_service.create_task(db, project.id, TaskCreate(title="Parent"))
    parent_id = parent.id
    child = await task_service.create_task(db, project.id, TaskCreate(title="Child"), parent_id=parent_id)
    child_id = child.id
    await task_service.update_task(db, child_id, TaskUpdate(is_completed=True))

    updated = await task_service.update_task(db, parent_id, TaskUpdate(is_completed=True))
    assert updated.is_completed is True
    assert updated.completed_at is not None


async def test_delete_task(db):
    project = await _make_project(db)
    task = await task_service.create_task(db, project.id, TaskCreate(title="Del"))
    await task_service.delete_task(db, task.id)

    with pytest.raises(NotFoundError):
        await task_service.get_task(db, task.id)


async def test_get_children(db):
    project = await _make_project(db)
    parent = await task_service.create_task(db, project.id, TaskCreate(title="Parent"))
    await task_service.create_task(db, project.id, TaskCreate(title="C1", priority=2), parent_id=parent.id)
    await task_service.create_task(db, project.id, TaskCreate(title="C2", priority=1), parent_id=parent.id)

    children = await task_service.get_children(db, parent.id)
    assert len(children) == 2
    assert children[0].title == "C2"  # priority 1 first


async def test_get_children_parent_not_found(db):
    with pytest.raises(NotFoundError):
        await task_service.get_children(db, 9999)
