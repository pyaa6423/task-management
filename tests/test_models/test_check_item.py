from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.task import Task
from app.models.check_item import CheckItem


async def test_create_check_item(db):
    project = Project(name="P")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 1")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    item = CheckItem(task_id=task.id, title="Check 1")
    db.add(item)
    await db.commit()
    await db.refresh(item)

    assert item.id is not None
    assert item.title == "Check 1"
    assert item.is_checked is False
    assert item.checked_at is None
    assert item.inputs == []
    assert item.outputs == []
    assert item.results == []
    assert item.evidences == []


async def test_check_item_with_json_fields(db):
    project = Project(name="P2")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 2")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    item = CheckItem(
        task_id=task.id,
        title="Check with data",
        inputs=["doc1", "doc2"],
        outputs=["report"],
        results=["pass"],
        evidences=["screenshot.png"],
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    assert item.inputs == ["doc1", "doc2"]
    assert item.outputs == ["report"]
    assert item.results == ["pass"]
    assert item.evidences == ["screenshot.png"]


async def test_check_item_relationship(db):
    project = Project(name="P3")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 3")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    item1 = CheckItem(task_id=task.id, title="Check A")
    item2 = CheckItem(task_id=task.id, title="Check B")
    db.add_all([item1, item2])
    await db.commit()

    stmt = select(Task).options(selectinload(Task.check_items)).where(Task.id == task.id)
    loaded_task = await db.scalar(stmt)
    assert len(loaded_task.check_items) == 2
    titles = {ci.title for ci in loaded_task.check_items}
    assert titles == {"Check A", "Check B"}


async def test_check_item_cascade_delete(db):
    project = Project(name="P4")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 4")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    item = CheckItem(task_id=task.id, title="Will be deleted")
    db.add(item)
    await db.commit()
    item_id = item.id

    await db.delete(task)
    await db.commit()

    result = await db.get(CheckItem, item_id)
    assert result is None


async def test_check_item_checked_state(db):
    project = Project(name="P5")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 5")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    now = datetime.now(timezone.utc)
    item = CheckItem(
        task_id=task.id,
        title="Checked item",
        is_checked=True,
        checked_at=now,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    assert item.is_checked is True
    assert item.checked_at is not None
