from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services import task_service

router = APIRouter(tags=["tasks"])


@router.get("/api/v1/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.get_tasks_by_project(db, project_id)


@router.post("/api/v1/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    project_id: int,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.create_task(db, project_id, data)


@router.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.get_task(db, task_id)


@router.put("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.update_task(db, task_id, data)


@router.delete("/api/v1/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    await task_service.delete_task(db, task_id)


@router.get("/api/v1/tasks/{task_id}/children", response_model=list[TaskResponse])
async def list_children(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.get_children(db, task_id)


@router.post("/api/v1/tasks/{task_id}/children", response_model=TaskResponse, status_code=201)
async def create_child(
    task_id: int,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    parent = await task_service.get_task(db, task_id)
    return await task_service.create_task(db, parent.project_id, data, parent_id=task_id)
