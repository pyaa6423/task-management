import pytest
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.task import Task


async def test_create_project(db):
    project = Project(name="Test Project", description="A test project")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.is_completed is False
    assert project.completed_at is None


async def test_project_has_tasks_relationship(db):
    project = Project(name="Project with tasks")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    task = Task(project_id=project.id, title="Task 1")
    db.add(task)
    await db.commit()

    stmt = select(Project).options(selectinload(Project.tasks)).where(Project.id == project.id)
    project = await db.scalar(stmt)
    assert len(project.tasks) == 1
    assert project.tasks[0].title == "Task 1"


async def test_project_completion_flag(db):
    project = Project(
        name="Completed Project",
        is_completed=True,
        completed_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    assert project.is_completed is True
    assert project.completed_at is not None


async def test_project_dates(db):
    project = Project(
        name="Dated Project",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    assert project.start_date == date(2026, 3, 1)
    assert project.end_date == date(2026, 3, 31)


async def test_project_team_members(db):
    project = Project(
        name="Team Project",
        team_members=["Alice", "Bob", "Charlie"],
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    assert project.team_members == ["Alice", "Bob", "Charlie"]
