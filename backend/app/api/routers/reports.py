"""Report endpoints (Strategy pattern selected by path parameter)."""

from fastapi import APIRouter

from app.api import mappers
from app.api.deps import PeriodDep, ReportServiceDep
from app.api.schemas import ErrorOut, ReportOut, ReportTypeOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportTypeOut], summary="Available report types")
def list_report_types(service: ReportServiceDep) -> list[ReportTypeOut]:
    """Every registered report strategy; the UI builds its picker from this list."""
    return [mappers.report_type(strategy) for strategy in service.available()]


@router.get(
    "/{report_type}",
    response_model=ReportOut,
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}},
    summary="Generate a report",
)
def get_report(report_type: str, service: ReportServiceDep, period: PeriodDep) -> ReportOut:
    """Run the report strategy registered under ``report_type`` for ``month``."""
    return mappers.report(service.generate(report_type, period))
