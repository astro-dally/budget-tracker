"""Account endpoints: sign up, sign in, current user, demo logins."""

from fastapi import APIRouter, status

from app.api import mappers
from app.api.deps import AuthServiceDep, ContainerDep, CurrentUser
from app.api.schemas import AuthOut, DemoAccountOut, ErrorOut, LoginIn, RegisterIn, UserOut
from app.application.auth_service import AuthResult
from app.infrastructure.demo_accounts import DEMO_PERSONAS

router = APIRouter(prefix="/auth", tags=["auth"])


def _out(result: AuthResult) -> AuthOut:
    return AuthOut(access_token=result.token, user=mappers.user(result.user))


@router.post(
    "/register",
    response_model=AuthOut,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorOut}, 422: {"model": ErrorOut}},
    summary="Create an account",
)
def register(body: RegisterIn, auth: AuthServiceDep) -> AuthOut:
    """Create an account with starter categories and keyword rules, and sign in."""
    return _out(auth.register(name=body.name, email=body.email, password=body.password))


@router.post(
    "/login",
    response_model=AuthOut,
    responses={401: {"model": ErrorOut}, 429: {"model": ErrorOut}},
    summary="Sign in",
)
def login(body: LoginIn, auth: AuthServiceDep) -> AuthOut:
    """Exchange e-mail and password for a bearer token. Repeated failures are throttled."""
    return _out(auth.login(email=body.email, password=body.password))


@router.get("/me", response_model=UserOut, responses={401: {"model": ErrorOut}})
def me(user: CurrentUser) -> UserOut:
    """The signed-in user."""
    return mappers.user(user)


@router.get("/demo-accounts", response_model=list[DemoAccountOut], summary="Demo logins")
def demo_accounts(container: ContainerDep) -> list[DemoAccountOut]:
    """Ready-made logins for trying the app (empty when demo data is disabled)."""
    if not container.settings.seed_demo_data:
        return []
    return [
        DemoAccountOut(
            name=p.name, email=p.email, password=p.password, role=p.role, tagline=p.tagline
        )
        for p in DEMO_PERSONAS
    ]
