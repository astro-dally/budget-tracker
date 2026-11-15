"""Budget endpoints."""

from fastapi import APIRouter, Response, status

from app.api import mappers
from app.api.deps import BudgetServiceDep, PeriodDep
from app.api.schemas import BudgetLimitIn, BudgetStatusOut, ErrorOut
from app.domain.money import Money

router = APIRouter(
    prefix="/budgets",
    tags=["budgets"],
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)


@router.get("", response_model=list[BudgetStatusOut], summary="Budget usage for a month")
def list_budgets(service: BudgetServiceDep, period: PeriodDep) -> list[BudgetStatusOut]:
    """Spent, remaining and health (ok / warning / exceeded) for every budget."""
    return [mappers.budget_status(status) for status in service.statuses(period)]


@router.put("/{category_id}", response_model=BudgetStatusOut, summary="Set a monthly limit")
def set_budget(
    category_id: str, body: BudgetLimitIn, service: BudgetServiceDep, period: PeriodDep
) -> BudgetStatusOut:
    """Create or change a category's limit. Lowering it may raise alerts immediately."""
    service.set_limit(category_id, Money(body.monthly_limit))
    status_for = next(s for s in service.statuses(period) if s.category.id == category_id)
    return mappers.budget_status(status_for)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def remove_budget(category_id: str, service: BudgetServiceDep) -> Response:
    """Remove a category's limit."""
    service.remove_limit(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
