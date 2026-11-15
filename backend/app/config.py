"""Application settings, read from environment variables or a ``.env`` file.

Pydantic is allowed here because configuration is an outer-layer concern;
the domain never sees this module.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import cached_property

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Typed configuration. Every field maps to an upper-case environment variable."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Budget Tracker API"
    log_level: str = "INFO"
    jwt_secret: str = "dev-only-change-me-in-production-0123456789abcdef"
    token_lifetime_hours: int = Field(default=24, ge=1, le=24 * 30)
    database_url: str = "sqlite:///./budget_tracker.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    auto_migrate: bool = True
    seed_demo_data: bool = True
    scheduler_enabled: bool = True
    recurring_job_interval_minutes: int = Field(default=60, ge=1)
    alert_thresholds: str = "80,100"
    notification_channels: str = "console,in_app,email,sms"
    categorization_order: str = "keyword,merchant,user_defined,default"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    alert_email_from: str = "alerts@budget-tracker.local"
    alert_sms_to: str | None = None

    @field_validator("alert_thresholds")
    @classmethod
    def _validate_thresholds(cls, value: str) -> str:
        try:
            parsed = [Decimal(item) for item in _split(value)]
        except InvalidOperation as exc:
            raise ValueError("ALERT_THRESHOLDS must be comma-separated numbers") from exc
        if not parsed or any(item <= 0 for item in parsed):
            raise ValueError("ALERT_THRESHOLDS must contain positive numbers")
        return value

    @cached_property
    def cors_origin_list(self) -> list[str]:
        """Allowed CORS origins."""
        return _split(self.cors_origins)

    @cached_property
    def alert_threshold_list(self) -> list[Decimal]:
        """Alert thresholds in ascending order."""
        return sorted(Decimal(item) for item in _split(self.alert_thresholds))

    @cached_property
    def notification_channel_list(self) -> list[str]:
        """Enabled notification channel names."""
        return _split(self.notification_channels)

    @cached_property
    def categorization_order_list(self) -> list[str]:
        """Categorisation handler names in chain order."""
        return _split(self.categorization_order)
