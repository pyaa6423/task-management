from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.deliverable import Deliverable
from app.models.project import Project
from app.schemas.deliverable import DeliverableCreate, DeliverableUpdate, VALID_STATUS
from app.exceptions import NotFoundError, ValidationError


def _validate_status(status: str) -> None:
    if status not in VALID_STATUS:
        raise ValidationError(f"status must be one of {VALID_STATUS}")


async def _get_or_404(db: AsyncSession, deliverable_id: int) -> Deliverable:
    stmt = (
        select(Deliverable)
        .options(selectinload(Deliverable.children).selectinload(Deliverable.children))
        .where(Deliverable.id == deliverable_id)
    )
    d = await db.scalar(stmt)
    if not d:
        raise NotFoundError("Deliverable", deliverable_id)
    return d


async def get_by_project(db: AsyncSession, project_id: int) -> list[Deliverable]:
    """Return top-level deliverables with children loaded (2-level deep)."""
    stmt = (
        select(Deliverable)
        .options(selectinload(Deliverable.children).selectinload(Deliverable.children))
        .where(Deliverable.project_id == project_id, Deliverable.parent_id.is_(None))
        .order_by(Deliverable.sort_order.asc(), Deliverable.created_at.asc())
    )
    return list((await db.scalars(stmt)).all())


async def get_deliverable(db: AsyncSession, deliverable_id: int) -> Deliverable:
    return await _get_or_404(db, deliverable_id)


async def create_deliverable(
    db: AsyncSession, project_id: int, data: DeliverableCreate
) -> Deliverable:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project", project_id)
    _validate_status(data.status)
    if data.parent_id is not None:
        parent = await db.get(Deliverable, data.parent_id)
        if not parent or parent.project_id != project_id:
            raise ValidationError("parent_id must be a deliverable in the same project")
        if parent.parent_id is not None:
            raise ValidationError("Nesting is limited to 2 levels")

    deliverable = Deliverable(project_id=project_id, **data.model_dump())
    db.add(deliverable)
    await db.commit()
    return await _get_or_404(db, deliverable.id)


async def update_deliverable(
    db: AsyncSession, deliverable_id: int, data: DeliverableUpdate
) -> Deliverable:
    deliverable = await _get_or_404(db, deliverable_id)
    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] is not None:
        _validate_status(update_data["status"])

    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        if new_parent_id == deliverable.id:
            raise ValidationError("Deliverable cannot be its own parent")
        if new_parent_id is not None:
            parent = await db.get(Deliverable, new_parent_id)
            if not parent or parent.project_id != deliverable.project_id:
                raise ValidationError("parent_id must be a deliverable in the same project")
            if parent.parent_id is not None:
                raise ValidationError("Nesting is limited to 2 levels")
            if deliverable.children:
                raise ValidationError("Cannot nest a deliverable that has children")

    for key, value in update_data.items():
        setattr(deliverable, key, value)

    await db.commit()
    return await _get_or_404(db, deliverable.id)


async def delete_deliverable(db: AsyncSession, deliverable_id: int) -> None:
    deliverable = await _get_or_404(db, deliverable_id)
    await db.delete(deliverable)
    await db.commit()
