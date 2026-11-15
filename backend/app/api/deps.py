"""FastAPI dependencies.

``CurrentUser`` resolves the bearer token to an active account. ``Scope``
wires that user's services; every router receives services typed by their
class, already bound to the signed-in user. ``AdminUser`` additionally
requires the admin role.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.admin_service import AdminService
from app.application.alert_service import AlertService
from app.application.auth_service import AuthService
from app.application.budget_service import BudgetService
from app.application.categorization_service import CategorizationService
from app.application.category_service import CategoryService
from app.application.dashboard_service import DashboardService
from app.application.ports import Clock
from app.application.recurring_service import RecurringService
from app.application.report_service import ReportService
from app.application.rule_service import RuleService
from app.application.transaction_service import TransactionService
from app.container import Container, UserScope
from app.domain.errors import AuthenticationError, PermissionDeniedError
from app.domain.money import Period
from app.domain.user import User
from app.infrastructure.realtime import AlertBroadcaster

_bearer = HTTPBearer(auto_error=False, description="Session token from /auth/login")


def get_container(request: Request) -> Container:
    """The composition root built at start-up."""
    return cast(Container, request.app.state.container)


ContainerDep = Annotated[Container, Depends(get_container)]


def _auth(c: ContainerDep) -> AuthService:
    return c.auth


AuthServiceDep = Annotated[AuthService, Depends(_auth)]


def _current_user(
    auth: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Sign in to continue")
    return auth.authenticate(credentials.credentials)


CurrentUser = Annotated[User, Depends(_current_user)]


def _admin_user(user: CurrentUser) -> User:
    if not user.is_admin:
        raise PermissionDeniedError("Administrator access is required")
    return user


AdminUser = Annotated[User, Depends(_admin_user)]


def _scope(c: ContainerDep, user: CurrentUser) -> UserScope:
    return c.scope_for(user)


ScopeDep = Annotated[UserScope, Depends(_scope)]


def _transactions(s: ScopeDep) -> TransactionService:
    return s.transactions


def _categories(s: ScopeDep) -> CategoryService:
    return s.categories


def _budgets(s: ScopeDep) -> BudgetService:
    return s.budgets


def _rules(s: ScopeDep) -> RuleService:
    return s.rules


def _recurring(s: ScopeDep) -> RecurringService:
    return s.recurring


def _reports(s: ScopeDep) -> ReportService:
    return s.reports


def _alerts(s: ScopeDep) -> AlertService:
    return s.alerts


def _categorization(s: ScopeDep) -> CategorizationService:
    return s.categorization


def _dashboard(s: ScopeDep) -> DashboardService:
    return s.dashboard


def _admin_service(c: ContainerDep) -> AdminService:
    return c.admin


def _clock(c: ContainerDep) -> Clock:
    return c.clock


def _broadcaster(c: ContainerDep) -> AlertBroadcaster:
    return c.broadcaster


TransactionServiceDep = Annotated[TransactionService, Depends(_transactions)]
CategoryServiceDep = Annotated[CategoryService, Depends(_categories)]
BudgetServiceDep = Annotated[BudgetService, Depends(_budgets)]
RuleServiceDep = Annotated[RuleService, Depends(_rules)]
RecurringServiceDep = Annotated[RecurringService, Depends(_recurring)]
ReportServiceDep = Annotated[ReportService, Depends(_reports)]
AlertServiceDep = Annotated[AlertService, Depends(_alerts)]
CategorizationServiceDep = Annotated[CategorizationService, Depends(_categorization)]
DashboardServiceDep = Annotated[DashboardService, Depends(_dashboard)]
AdminServiceDep = Annotated[AdminService, Depends(_admin_service)]
ClockDep = Annotated[Clock, Depends(_clock)]
BroadcasterDep = Annotated[AlertBroadcaster, Depends(_broadcaster)]


def _period(
    clock: ClockDep,
    month: Annotated[
        str | None,
        Query(
            pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
            description="Month as YYYY-MM; defaults to the current month",
        ),
    ] = None,
) -> Period:
    return Period.parse(month) if month else Period.of(clock.today())


PeriodDep = Annotated[Period, Depends(_period)]
