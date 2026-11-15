"""Dashboard endpoint."""

from fastapi import APIRouter

from app.api import mappers
from app.api.deps import DashboardServiceDep, PeriodDep
from app.api.schemas import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut, summary="Dashboard overview for a month")
def get_dashboard(service: DashboardServiceDep, period: PeriodDep) -> DashboardOut:
    """Summary cards, charts, budget progress, recent and upcoming payments."""
    return mappers.dashboard(service.overview(period))
