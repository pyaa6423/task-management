from datetime import date, datetime, timedelta
from calendar import monthrange
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.report import ReportResponse
from app.services import report_service

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/daily", response_model=ReportResponse)
async def daily_report(
    target_date: date = Query(alias="date"),
    member: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    start = datetime(target_date.year, target_date.month, target_date.day)
    end = start + timedelta(days=1)
    items = await report_service.get_completed_items(db, start, end, member)
    return ReportResponse(
        period="daily",
        start=str(target_date),
        end=str(target_date),
        items=items,
        total_count=len(items),
    )


@router.get("/weekly", response_model=ReportResponse)
async def weekly_report(
    start_date: date,
    end_date: date,
    member: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    start = datetime(start_date.year, start_date.month, start_date.day)
    end = datetime(end_date.year, end_date.month, end_date.day) + timedelta(days=1)
    items = await report_service.get_completed_items(db, start, end, member)
    return ReportResponse(
        period="weekly",
        start=str(start_date),
        end=str(end_date),
        items=items,
        total_count=len(items),
    )


@router.get("/monthly", response_model=ReportResponse)
async def monthly_report(
    year: int,
    month: int,
    member: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    start = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    end = datetime(year, month, last_day) + timedelta(days=1)
    items = await report_service.get_completed_items(db, start, end, member)
    return ReportResponse(
        period="monthly",
        start=f"{year}-{month:02d}-01",
        end=f"{year}-{month:02d}-{last_day:02d}",
        items=items,
        total_count=len(items),
    )
