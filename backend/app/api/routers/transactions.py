"""Transaction endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api import mappers
from app.api.deps import TransactionServiceDep
from app.api.schemas import ErrorOut, TransactionIn, TransactionOut, TransactionPageOut
from app.application.queries import MAX_PAGE_SIZE, SortDirection, SortField, TransactionQuery
from app.application.transaction_service import TransactionInput
from app.domain.enums import TransactionType
from app.domain.money import Money, Period

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)


def _to_input(body: TransactionIn) -> TransactionInput:
    return TransactionInput(
        type=body.type,
        amount=Money(body.amount),
        description=body.description,
        occurred_on=body.occurred_on,
        category_id=body.category_id,
    )


@router.get("", response_model=TransactionPageOut, summary="List transactions")
def list_transactions(
    service: TransactionServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
    type: TransactionType | None = None,
    category_id: str | None = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: SortField = SortField.OCCURRED_ON,
    sort_direction: SortDirection = SortDirection.DESC,
) -> TransactionPageOut:
    """Search, filter, sort and paginate transactions. ``month`` overrides the date range."""
    if month:
        period = Period.parse(month)
        date_from, date_to = period.start, period.end
    query = TransactionQuery(
        page=page,
        page_size=page_size,
        type=type,
        category_id=category_id,
        search=search or None,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return mappers.transaction_page(service.search(query))


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED, summary="Add")
def create_transaction(body: TransactionIn, service: TransactionServiceDep) -> TransactionOut:
    """Record a transaction. Expenses without a category are auto-categorised."""
    return mappers.transaction(service.record(_to_input(body)))


@router.get("/{transaction_id}", response_model=TransactionOut, summary="Get one")
def get_transaction(transaction_id: str, service: TransactionServiceDep) -> TransactionOut:
    """Fetch a single transaction."""
    return mappers.transaction(service.get(transaction_id))


@router.put("/{transaction_id}", response_model=TransactionOut, summary="Replace")
def update_transaction(
    transaction_id: str, body: TransactionIn, service: TransactionServiceDep
) -> TransactionOut:
    """Replace a transaction; the affected budget is re-checked."""
    return mappers.transaction(service.update(transaction_id, _to_input(body)))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_transaction(transaction_id: str, service: TransactionServiceDep) -> Response:
    """Delete a transaction."""
    service.delete(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
