from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import SeasonalityMetricOut, InsightLogOut
from app.auth.auth import get_current_user
from app.services.insight_service import InsightService

router = APIRouter(prefix="/api/insights", tags=["Insights"])


@router.get("/refresh")
def refresh_insights(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    insights = service.generate_insights()
    return {"message": f"{len(insights)} insights generated", "insights": insights}


@router.get("/active", response_model=list[InsightLogOut])
def get_active_insights(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    return service.get_active_insights()


@router.get("/seasonality/top-products-day", response_model=list[dict])
def get_top_products_by_day(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    return service.calculate_top_products_by_day()


@router.get("/seasonality/top-products-month", response_model=list[dict])
def get_top_products_by_month(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    return service.calculate_top_products_by_month()


@router.get("/seasonality/peak-hours", response_model=list[dict])
def get_peak_hours(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    return service.calculate_peak_hours()


@router.get("/seasonality/top-clients", response_model=list[dict])
def get_top_clients(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    return service.calculate_top_clients()


@router.get("/seasonality/category-consumption", response_model=list[dict])
def get_category_consumption(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InsightService(db)
    return service.calculate_category_consumption()
