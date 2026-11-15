"""Administrator endpoints. Every route requires the admin role."""

from fastapi import APIRouter

from app.api import mappers
from app.api.deps import AdminServiceDep, AdminUser
from app.api.schemas import AdminUserOut, AdminUserUpdateIn, ErrorOut, PlatformOverviewOut

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={401: {"model": ErrorOut}, 403: {"model": ErrorOut}},
)


@router.get("/overview", response_model=PlatformOverviewOut, summary="Platform statistics")
def overview(actor: AdminUser, service: AdminServiceDep) -> PlatformOverviewOut:
    """Users, activity, money tracked and alerts across the platform."""
    return mappers.platform_overview(service.overview(actor))


@router.get("/users", response_model=list[AdminUserOut], summary="All users")
def list_users(actor: AdminUser, service: AdminServiceDep) -> list[AdminUserOut]:
    """Every account with activity counts, newest first."""
    return [mappers.admin_user(summary) for summary in service.list_users(actor)]


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserOut,
    responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut}},
    summary="Update a user",
)
def update_user(
    user_id: str, body: AdminUserUpdateIn, actor: AdminUser, service: AdminServiceDep
) -> AdminUserOut:
    """Activate or deactivate an account, or change its role. You can't change yourself."""
    return mappers.admin_user(
        service.update_user(actor, user_id, is_active=body.is_active, role=body.role)
    )
