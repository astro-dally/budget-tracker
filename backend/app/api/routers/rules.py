"""Keyword rule endpoints."""

from fastapi import APIRouter, Response, status

from app.api import mappers
from app.api.deps import RuleServiceDep
from app.api.schemas import ErrorOut, RuleIn, RuleOut

router = APIRouter(
    prefix="/rules",
    tags=["category rules"],
    responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)


@router.get("", response_model=list[RuleOut], summary="List keyword rules")
def list_rules(service: RuleServiceDep) -> list[RuleOut]:
    """All keyword → category rules."""
    return [mappers.rule(rule) for rule in service.list_all()]


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(body: RuleIn, service: RuleServiceDep) -> RuleOut:
    """Add a keyword rule."""
    return mappers.rule(service.create(body.keyword, body.category_id))


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: str, body: RuleIn, service: RuleServiceDep) -> RuleOut:
    """Change a rule."""
    return mappers.rule(service.update(rule_id, body.keyword, body.category_id))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_rule(rule_id: str, service: RuleServiceDep) -> Response:
    """Delete a rule."""
    service.delete(rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
