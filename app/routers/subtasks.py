from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.subtask import SubTaskCreate, SubTaskUpdate, SubTaskResponse
from app.services import subtask_service

router = APIRouter(tags=["subtasks"])


@router.get("/api/v1/tasks/{task_id}/subtasks", response_model=list[SubTaskResponse])
async def list_subtasks(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await subtask_service.get_subtasks_by_task(db, task_id)


@router.post("/api/v1/tasks/{task_id}/subtasks", response_model=SubTaskResponse, status_code=201)
async def create_subtask(
    task_id: int,
    data: SubTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    return await subtask_service.create_subtask(db, task_id, data)


@router.get("/api/v1/subtasks/{subtask_id}", response_model=SubTaskResponse)
async def get_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await subtask_service.get_subtask(db, subtask_id)


@router.put("/api/v1/subtasks/{subtask_id}", response_model=SubTaskResponse)
async def update_subtask(
    subtask_id: int,
    data: SubTaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await subtask_service.update_subtask(db, subtask_id, data)


@router.delete("/api/v1/subtasks/{subtask_id}", status_code=204)
async def delete_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
):
    await subtask_service.delete_subtask(db, subtask_id)
