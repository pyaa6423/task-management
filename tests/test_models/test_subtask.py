import pytest
from datetime import datetime, timezone
from app.models.project import Project
from app.models.task import Task
from app.models.subtask import SubTask


async def _make_task(db):
    project = Project(name="P")
    db.add(project)
    await db.commit()
    await db.refresh(project)
    task = Task(project_id=project.id, title="T")
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def test_create_subtask(db):
    task = await _make_task(db)
    subtask = SubTask(task_id=task.id, title="SubTask 1")
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)

    assert subtask.id is not None
    assert subtask.title == "SubTask 1"
    assert subtask.is_completed is False


async def test_subtask_belongs_to_task(db):
    task = await _make_task(db)
    subtask = SubTask(task_id=task.id, title="Sub")
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)

    assert subtask.task_id == task.id


async def test_subtask_priority(db):
    task = await _make_task(db)
    s1 = SubTask(task_id=task.id, title="Low", priority=3)
    s2 = SubTask(task_id=task.id, title="High", priority=1)
    db.add_all([s1, s2])
    await db.commit()

    from sqlalchemy import select
    subs = (await db.scalars(
        select(SubTask).where(SubTask.task_id == task.id).order_by(SubTask.priority.asc())
    )).all()
    assert subs[0].title == "High"
    assert subs[1].title == "Low"


async def test_subtask_completion(db):
    task = await _make_task(db)
    now = datetime.now(timezone.utc)
    subtask = SubTask(
        task_id=task.id,
        title="Done sub",
        is_completed=True,
        completed_at=now,
    )
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)

    assert subtask.is_completed is True
    assert subtask.completed_at is not None
