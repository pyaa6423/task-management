import pytest
from datetime import date
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services import project_service
from app.exceptions import NotFoundError, ConflictError
from app.models.task import Task


async def test_create_project(db):
    data = ProjectCreate(name="New Project", description="desc", start_date=date(2026, 3, 1))
    project = await project_service.create_project(db, data)

    assert project.id is not None
    assert project.name == "New Project"


async def test_get_project(db):
    data = ProjectCreate(name="Get Me")
    created = await project_service.create_project(db, data)
    fetched = await project_service.get_project(db, created.id)

    assert fetched.name == "Get Me"


async def test_get_project_not_found(db):
    with pytest.raises(NotFoundError):
        await project_service.get_project(db, 9999)


async def test_list_projects(db):
    await project_service.create_project(db, ProjectCreate(name="P1"))
    await project_service.create_project(db, ProjectCreate(name="P2"))
    projects = await project_service.get_projects(db)

    assert len(projects) >= 2


async def test_update_project(db):
    created = await project_service.create_project(db, ProjectCreate(name="Old Name"))
    updated = await project_service.update_project(db, created.id, ProjectUpdate(name="New Name"))

    assert updated.name == "New Name"


async def test_complete_project_with_incomplete_tasks(db):
    project = await project_service.create_project(db, ProjectCreate(name="P"))
    project_id = project.id
    task = Task(project_id=project_id, title="Incomplete task")
    db.add(task)
    await db.commit()
    db.expire_all()

    with pytest.raises(ConflictError):
        await project_service.update_project(db, project_id, ProjectUpdate(is_completed=True))


async def test_complete_project_all_tasks_done(db):
    project = await project_service.create_project(db, ProjectCreate(name="P"))
    task = Task(project_id=project.id, title="Done task", is_completed=True)
    db.add(task)
    await db.commit()

    updated = await project_service.update_project(db, project.id, ProjectUpdate(is_completed=True))
    assert updated.is_completed is True
    assert updated.completed_at is not None


async def test_delete_project(db):
    created = await project_service.create_project(db, ProjectCreate(name="Delete me"))
    await project_service.delete_project(db, created.id)

    with pytest.raises(NotFoundError):
        await project_service.get_project(db, created.id)
