"""Use cases for administrators: platform overview and user management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.application.ports import Clock, PlatformStatsReader, UserActivity, UserRepository
from app.domain.enums import UserRole
from app.domain.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.domain.money import Money
from app.domain.user import User

SERIES_DAYS = 14
_NO_ACTIVITY = UserActivity(transaction_count=0, category_count=0, last_transaction_on=None)


@dataclass(frozen=True, slots=True)
class DailyCount:
    """A count for one day, for charts."""

    day: date
    count: int


@dataclass(frozen=True, slots=True)
class PlatformOverview:
    """Headline numbers for the admin dashboard."""

    total_users: int
    active_users: int
    admins: int
    new_users_7d: int
    transactions: int
    expense_volume: Money
    alerts_30d: int
    signups_by_day: list[DailyCount]
    activity_by_day: list[DailyCount]


@dataclass(frozen=True, slots=True)
class UserSummary:
    """A user with their activity, for the admin user list."""

    user: User
    activity: UserActivity


class AdminService:
    """Read platform statistics and manage accounts. Every method requires an admin."""

    def __init__(self, users: UserRepository, stats: PlatformStatsReader, clock: Clock) -> None:
        self._users = users
        self._stats = stats
        self._clock = clock

    def overview(self, actor: User) -> PlatformOverview:
        """Platform-wide numbers and 14-day series."""
        self._require_admin(actor)
        users = self._users.list_all()
        today = self._clock.today()
        start = today - timedelta(days=SERIES_DAYS - 1)
        signups: dict[date, int] = {}
        for user in users:
            day = user.created_at.date()
            signups[day] = signups.get(day, 0) + 1
        activity = self._stats.transactions_by_day(start)
        days = [start + timedelta(days=offset) for offset in range(SERIES_DAYS)]
        return PlatformOverview(
            total_users=len(users),
            active_users=sum(u.is_active for u in users),
            admins=sum(u.is_admin for u in users),
            new_users_7d=sum(u.created_at.date() > today - timedelta(days=7) for u in users),
            transactions=self._stats.transaction_count(),
            expense_volume=self._stats.expense_volume(),
            alerts_30d=self._stats.alerts_since(self._clock.now() - timedelta(days=30)),
            signups_by_day=[DailyCount(day, signups.get(day, 0)) for day in days],
            activity_by_day=[DailyCount(day, activity.get(day, 0)) for day in days],
        )

    def list_users(self, actor: User) -> list[UserSummary]:
        """Every user with activity, newest first."""
        self._require_admin(actor)
        activity = self._stats.activity_by_user()
        users = sorted(self._users.list_all(), key=lambda u: u.created_at, reverse=True)
        return [UserSummary(u, activity.get(u.id, _NO_ACTIVITY)) for u in users]

    def update_user(
        self,
        actor: User,
        user_id: str,
        *,
        is_active: bool | None = None,
        role: UserRole | None = None,
    ) -> UserSummary:
        """Activate/deactivate an account or change its role. Admins can't change themselves."""
        self._require_admin(actor)
        if user_id == actor.id:
            raise ConflictError("You can't change your own status or role")
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError("User", user_id)
        if is_active is not None:
            user = user.with_status(active=is_active)
        if role is not None:
            user = user.with_role(role)
        self._users.update(user)
        return UserSummary(user, self._stats.activity_by_user().get(user.id, _NO_ACTIVITY))

    @staticmethod
    def _require_admin(actor: User) -> None:
        if not actor.is_admin:
            raise PermissionDeniedError("Administrator access is required")
