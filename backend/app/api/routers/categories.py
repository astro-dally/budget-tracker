"""Category endpoints."""

from fastapi import APIRouter, Response, status

from app.api import mappers
from app.api.deps import CategoryServiceDep
from app.api.schemas import CategoryIn, CategoryOut, ErrorOut
from app.application.category_service import CategoryInput
from app.domain.money import Money

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)


def _to_input(body: CategoryIn) -> CategoryInput:
    limit = Money(body.monthly_limit) if body.monthly_limit is not None else None
    return CategoryInput(name=body.name, color=body.color, icon=body.icon, monthly_limit=limit)


@router.get("", response_model=list[CategoryOut], summary="List categories")
def list_categories(service: CategoryServiceDep) -> list[CategoryOut]:
    """All categories with their monthly limits."""
    return [mappers.category(details) for details in service.list_all()]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryIn, service: CategoryServiceDep) -> CategoryOut:
    """Create a category, optionally with a monthly budget."""
    return mappers.category(service.create(_to_input(body)))


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: str, service: CategoryServiceDep) -> CategoryOut:
    """Fetch one category."""
    return mappers.category(service.get(category_id))


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: str, body: CategoryIn, service: CategoryServiceDep) -> CategoryOut:
    """Update a category. Omitting ``monthly_limit`` removes its budget."""
    return mappers.category(service.update(category_id, _to_input(body)))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_category(category_id: str, service: CategoryServiceDep) -> Response:
    """Delete a category; its transactions move to *Uncategorized*."""
    service.delete(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
