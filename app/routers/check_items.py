from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.check_item import CheckItemCreate, CheckItemUpdate, CheckItemResponse
from app.services import check_item_service
from app.services import task_service

router = APIRouter(tags=["check_items"])
templates = Jinja2Templates(directory="app/templates")


# HTML page
@router.get("/tasks/{task_id}/checks", response_class=HTMLResponse)
async def checks_page(
    request: Request,
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(db, task_id)
    check_items = await check_item_service.get_check_items_by_task(db, task_id)
    # Serialize to dicts for Jinja2 tojson filter
    items_data = [
        {
            "id": ci.id, "task_id": ci.task_id, "title": ci.title,
            "is_checked": ci.is_checked,
            "checked_at": ci.checked_at.isoformat() if ci.checked_at else None,
            "inputs": ci.inputs or [], "outputs": ci.outputs or [],
            "results": ci.results or [], "evidences": ci.evidences or [],
            "created_at": ci.created_at.isoformat() if ci.created_at else None,
            "updated_at": ci.updated_at.isoformat() if ci.updated_at else None,
        }
        for ci in check_items
    ]
    return templates.TemplateResponse(request, "checks.html", {
        "task": task,
        "check_items": items_data,
    })


# API endpoints
@router.get("/api/v1/tasks/{task_id}/checks", response_model=list[CheckItemResponse])
async def list_check_items(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await check_item_service.get_check_items_by_task(db, task_id)


@router.post("/api/v1/tasks/{task_id}/checks", response_model=CheckItemResponse, status_code=201)
async def create_check_item(
    task_id: int,
    data: CheckItemCreate,
    db: AsyncSession = Depends(get_db),
):
    return await check_item_service.create_check_item(db, task_id, data)


@router.get("/api/v1/checks/{check_item_id}", response_model=CheckItemResponse)
async def get_check_item(
    check_item_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await check_item_service.get_check_item(db, check_item_id)


@router.put("/api/v1/checks/{check_item_id}", response_model=CheckItemResponse)
async def update_check_item(
    check_item_id: int,
    data: CheckItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await check_item_service.update_check_item(db, check_item_id, data)


@router.delete("/api/v1/checks/{check_item_id}", status_code=204)
async def delete_check_item(
    check_item_id: int,
    db: AsyncSession = Depends(get_db),
):
    await check_item_service.delete_check_item(db, check_item_id)
