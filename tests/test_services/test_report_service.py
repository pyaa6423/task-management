import pytest
from datetime import datetime, timezone
from app.models.project import Project
from app.models.task import Task
from app.models.subtask import SubTask
from app.services import report_service


async def test_get_completed_items_tasks(db):
    project = Project(name="Report Project")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(
        project_id=project.id,
        title="Done Task",
        assigned_member="Alice",
        is_completed=True,
        completed_at=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
    )
    db.add(task)
    await db.commit()

    items = await report_service.get_completed_items(
        db,
        start=datetime(2026, 3, 15, tzinfo=timezone.utc),
        end=datetime(2026, 3, 16, tzinfo=timezone.utc),
    )

    assert len(items) == 1
    assert items[0].item_type == "task"
    assert items[0].title == "Done Task"
    assert items[0].project_name == "Report Project"


async def test_get_completed_items_subtasks(db):
    project = Project(name="P")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Parent Task")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    subtask = SubTask(
        task_id=task.id,
        title="Done Sub",
        is_completed=True,
        completed_at=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
    )
    db.add(subtask)
    await db.commit()

    items = await report_service.get_completed_items(
        db,
        start=datetime(2026, 3, 15, tzinfo=timezone.utc),
        end=datetime(2026, 3, 16, tzinfo=timezone.utc),
    )

    assert len(items) == 1
    assert items[0].item_type == "subtask"
    assert items[0].task_title == "Parent Task"


async def test_get_completed_items_member_filter(db):
    project = Project(name="P")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    t1 = Task(
        project_id=project.id, title="T1", assigned_member="Alice",
        is_completed=True, completed_at=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
    )
    t2 = Task(
        project_id=project.id, title="T2", assigned_member="Bob",
        is_completed=True, completed_at=datetime(2026, 3, 15, 11, 0, tzinfo=timezone.utc),
    )
    db.add_all([t1, t2])
    await db.commit()

    items = await report_service.get_completed_items(
        db,
        start=datetime(2026, 3, 15, tzinfo=timezone.utc),
        end=datetime(2026, 3, 16, tzinfo=timezone.utc),
        member="Alice",
    )

    assert len(items) == 1
    assert items[0].assigned_member == "Alice"


async def test_get_completed_items_out_of_range(db):
    project = Project(name="P")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(
        project_id=project.id, title="Old Task",
        is_completed=True, completed_at=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc),
    )
    db.add(task)
    await db.commit()

    items = await report_service.get_completed_items(
        db,
        start=datetime(2026, 3, 15, tzinfo=timezone.utc),
        end=datetime(2026, 3, 16, tzinfo=timezone.utc),
    )

    assert len(items) == 0
