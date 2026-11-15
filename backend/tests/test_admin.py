"""Administration: overview statistics and user management rules."""

from datetime import UTC, date, datetime

import pytest

from app.application.admin_service import AdminService
from app.application.ports import UserActivity
from app.domain.enums import UserRole
from app.domain.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.domain.user import User
from tests.fakes import FixedClock, InMemoryPlatformStats, InMemoryUserRepository


def make_user(email: str, role: UserRole = UserRole.USER, day: int = 10) -> User:
    return User.create(
        email=email,
        name=email.split("@", maxsplit=1)[0],
        password_hash="x",
        created_at=datetime(2026, 11, day, 9, tzinfo=UTC),
        role=role,
    )


@pytest.fixture
def setup() -> tuple[AdminService, User, User]:
    users = InMemoryUserRepository()
    admin = make_user("admin@x.dev", UserRole.ADMIN, day=1)
    member = make_user("member@x.dev", day=13)
    users.add(admin)
    users.add(member)
    stats = InMemoryPlatformStats({member.id: UserActivity(7, 9, date(2026, 11, 13))})
    return AdminService(users, stats, FixedClock(date(2026, 11, 14))), admin, member


def test_overview_counts_users_and_builds_14_day_series(setup) -> None:  # type: ignore[no-untyped-def]
    service, admin, _ = setup
    overview = service.overview(admin)
    assert (overview.total_users, overview.active_users, overview.admins) == (2, 2, 1)
    assert overview.new_users_7d == 1
    assert len(overview.signups_by_day) == 14
    assert overview.signups_by_day[-2].count == 1
    assert overview.transactions == 7


def test_users_listed_newest_first_with_activity(setup) -> None:  # type: ignore[no-untyped-def]
    service, admin, member = setup
    listed = service.list_users(admin)
    assert [s.user.id for s in listed] == [member.id, admin.id]
    assert listed[0].activity.transaction_count == 7
    assert listed[1].activity.transaction_count == 0


def test_admin_can_deactivate_and_promote(setup) -> None:  # type: ignore[no-untyped-def]
    service, admin, member = setup
    updated = service.update_user(admin, member.id, is_active=False, role=UserRole.ADMIN)
    assert (updated.user.is_active, updated.user.role) == (False, UserRole.ADMIN)


def test_admins_cannot_change_themselves(setup) -> None:  # type: ignore[no-untyped-def]
    service, admin, _ = setup
    with pytest.raises(ConflictError):
        service.update_user(admin, admin.id, is_active=False)


def test_non_admins_are_refused_everywhere(setup) -> None:  # type: ignore[no-untyped-def]
    service, _, member = setup
    with pytest.raises(PermissionDeniedError):
        service.overview(member)
    with pytest.raises(PermissionDeniedError):
        service.list_users(member)
    with pytest.raises(PermissionDeniedError):
        service.update_user(member, member.id, is_active=False)


def test_unknown_user(setup) -> None:  # type: ignore[no-untyped-def]
    service, admin, _ = setup
    with pytest.raises(NotFoundError):
        service.update_user(admin, "missing", is_active=True)
