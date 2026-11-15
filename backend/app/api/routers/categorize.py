"""Auto-categorisation endpoint used for live suggestions in the UI."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api import mappers
from app.api.deps import CategorizationServiceDep
from app.api.schemas import ErrorOut, SuggestionOut

router = APIRouter(prefix="/categorize", tags=["categorisation"])


@router.get(
    "/suggest",
    response_model=SuggestionOut,
    responses={422: {"model": ErrorOut}},
    summary="Suggest a category for a description",
)
def suggest_category(
    service: CategorizationServiceDep,
    description: Annotated[str, Query(min_length=1, max_length=200)],
) -> SuggestionOut:
    """Run the categorisation chain without saving anything."""
    return mappers.suggestion(service.suggest(description))
