import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.task import Task
from app.models.subtask import SubTask


async def test_create_task(db):
    project = Project(name="P1")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 1", priority=1)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    assert task.id is not None
    assert task.title == "Task 1"
    assert task.priority == 1
    assert task.is_completed is False


async def test_task_has_subtasks_relationship(db):
    project = Project(name="P2")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task with subtasks")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    subtask = SubTask(task_id=task.id, title="SubTask 1")
    db.add(subtask)
    await db.commit()

    stmt = select(Task).options(selectinload(Task.subtasks)).where(Task.id == task.id)
    task = await db.scalar(stmt)
    assert len(task.subtasks) == 1
    assert task.subtasks[0].title == "SubTask 1"


async def test_task_priority_ordering(db):
    project = Project(name="P3")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    t1 = Task(project_id=project.id, title="Low", priority=3)
    t2 = Task(project_id=project.id, title="High", priority=1)
    t3 = Task(project_id=project.id, title="Medium", priority=2)
    db.add_all([t1, t2, t3])
    await db.commit()

    from sqlalchemy import select
    tasks = (await db.scalars(
        select(Task).where(Task.project_id == project.id).order_by(Task.priority.asc())
    )).all()
    assert [t.title for t in tasks] == ["High", "Medium", "Low"]


async def test_task_belongs_to_project(db):
    project = Project(name="P4")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Linked task")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    assert task.project_id == project.id


async def test_task_completion(db):
    project = Project(name="P5")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    now = datetime.now(timezone.utc)
    task = Task(
        project_id=project.id,
        title="Done task",
        is_completed=True,
        completed_at=now,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    assert task.is_completed is True
    assert task.completed_at is not None
