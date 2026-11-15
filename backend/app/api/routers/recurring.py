"""Recurring payment endpoints."""

from fastapi import APIRouter, Response, status

from app.api import mappers
from app.api.deps import ClockDep, RecurringServiceDep
from app.api.schemas import ErrorOut, GenerationResultOut, RecurringIn, RecurringOut
from app.application.recurring_service import RecurringInput
from app.domain.money import Money
from app.domain.recurrence import RecurringPayment

router = APIRouter(
    prefix="/recurring",
    tags=["recurring payments"],
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)


def _out(payment: RecurringPayment, clock: ClockDep) -> RecurringOut:
    return mappers.recurring(payment, payment.next_due(clock.today()))


@router.get("", response_model=list[RecurringOut], summary="List recurring payments")
def list_recurring(service: RecurringServiceDep, clock: ClockDep) -> list[RecurringOut]:
    """All recurring payments with their next due date."""
    return [_out(payment, clock) for payment in service.list_all()]


@router.post("", response_model=RecurringOut, status_code=status.HTTP_201_CREATED)
def create_recurring(
    body: RecurringIn, service: RecurringServiceDep, clock: ClockDep
) -> RecurringOut:
    """Create a recurring payment; occurrences already due are generated immediately."""
    payment = service.create(
        RecurringInput(
            description=body.description,
            amount=Money(body.amount),
            type=body.type,
            frequency=body.frequency,
            start_date=body.start_date,
            end_date=body.end_date,
            category_id=body.category_id,
        )
    )
    return _out(payment, clock)


@router.post("/run", response_model=GenerationResultOut, summary="Generate due transactions now")
def run_generation(service: RecurringServiceDep) -> GenerationResultOut:
    """Run the (idempotent) generation job on demand; the scheduler also runs it."""
    return GenerationResultOut(created=service.generate_due())


@router.get("/{recurring_id}", response_model=RecurringOut)
def get_recurring(recurring_id: str, service: RecurringServiceDep, clock: ClockDep) -> RecurringOut:
    """Fetch one recurring payment."""
    return _out(service.get(recurring_id), clock)


@router.post("/{recurring_id}/pause", response_model=RecurringOut)
def pause_recurring(
    recurring_id: str, service: RecurringServiceDep, clock: ClockDep
) -> RecurringOut:
    """Stop generating transactions."""
    return _out(service.pause(recurring_id), clock)


@router.post("/{recurring_id}/resume", response_model=RecurringOut)
def resume_recurring(
    recurring_id: str, service: RecurringServiceDep, clock: ClockDep
) -> RecurringOut:
    """Resume from today without back-filling the paused period."""
    return _out(service.resume(recurring_id), clock)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_recurring(recurring_id: str, service: RecurringServiceDep) -> Response:
    """Delete a recurring payment (generated transactions are kept)."""
    service.delete(recurring_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
