from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.check_item import CheckItem
from app.models.task import Task
from app.schemas.check_item import CheckItemCreate, CheckItemUpdate
from app.exceptions import NotFoundError


async def get_check_items_by_task(db: AsyncSession, task_id: int) -> list[CheckItem]:
    task = await db.get(Task, task_id)
    if not task:
        raise NotFoundError("Task", task_id)

    stmt = (
        select(CheckItem)
        .where(CheckItem.task_id == task_id)
        .order_by(CheckItem.created_at.asc())
    )
    return list((await db.scalars(stmt)).all())


async def get_check_item(db: AsyncSession, check_item_id: int) -> CheckItem:
    item = await db.get(CheckItem, check_item_id)
    if not item:
        raise NotFoundError("CheckItem", check_item_id)
    return item


async def create_check_item(db: AsyncSession, task_id: int, data: CheckItemCreate) -> CheckItem:
    task = await db.get(Task, task_id)
    if not task:
        raise NotFoundError("Task", task_id)

    item = CheckItem(task_id=task_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_check_item(db: AsyncSession, check_item_id: int, data: CheckItemUpdate) -> CheckItem:
    item = await get_check_item(db, check_item_id)
    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_checked") is True and not item.is_checked:
        update_data["checked_at"] = datetime.now(timezone.utc)
    elif update_data.get("is_checked") is False:
        update_data["checked_at"] = None

    for key, value in update_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item


async def delete_check_item(db: AsyncSession, check_item_id: int) -> None:
    item = await get_check_item(db, check_item_id)
    await db.delete(item)
    await db.commit()
