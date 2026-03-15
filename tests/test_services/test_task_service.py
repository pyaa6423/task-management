import pytest
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import project_service, task_service
from app.exceptions import NotFoundError, ConflictError
from app.models.subtask import SubTask


async def _make_project(db):
    return await project_service.create_project(db, ProjectCreate(name="P"))


async def test_create_task(db):
    project = await _make_project(db)
    data = TaskCreate(title="New Task", priority=1)
    task = await task_service.create_task(db, project.id, data)

    assert task.id is not None
    assert task.title == "New Task"
    assert task.project_id == project.id


async def test_create_task_project_not_found(db):
    with pytest.raises(NotFoundError):
        await task_service.create_task(db, 9999, TaskCreate(title="X"))


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


async def test_update_task(db):
    project = await _make_project(db)
    task = await task_service.create_task(db, project.id, TaskCreate(title="Old"))
    updated = await task_service.update_task(db, task.id, TaskUpdate(title="New"))
    assert updated.title == "New"


async def test_complete_task_with_incomplete_subtasks(db):
    project = await _make_project(db)
    task = await task_service.create_task(db, project.id, TaskCreate(title="T"))
    task_id = task.id
    subtask = SubTask(task_id=task_id, title="Incomplete sub")
    db.add(subtask)
    await db.commit()
    db.expire_all()

    with pytest.raises(ConflictError):
        await task_service.update_task(db, task_id, TaskUpdate(is_completed=True))


async def test_complete_task_all_subtasks_done(db):
    project = await _make_project(db)
    task = await task_service.create_task(db, project.id, TaskCreate(title="T"))
    subtask = SubTask(task_id=task.id, title="Done sub", is_completed=True)
    db.add(subtask)
    await db.commit()

    updated = await task_service.update_task(db, task.id, TaskUpdate(is_completed=True))
    assert updated.is_completed is True
    assert updated.completed_at is not None


async def test_delete_task(db):
    project = await _make_project(db)
    task = await task_service.create_task(db, project.id, TaskCreate(title="Del"))
    await task_service.delete_task(db, task.id)

    with pytest.raises(NotFoundError):
        await task_service.get_task(db, task.id)
