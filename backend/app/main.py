"""FastAPI application factory.

Run with ``uvicorn app.main:create_app --factory``. Using a factory (rather
than a module-level ``app``) means nothing is wired at import time: the
container is built inside the lifespan, and tests create isolated apps.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routers import api_router
from app.application.ports import Clock
from app.config import Settings
from app.container import build_container
from app.infrastructure.persistence.migrations import upgrade_database
from app.infrastructure.seed import seed_demo_accounts

API_PREFIX = "/api/v1"

DESCRIPTION = """
Personal Budget Tracker with Smart Spending Alerts.

* Accounts with JWT sessions; each user's data is isolated
* Admin console for platform statistics and user management
* Auto-categorisation (Chain of Responsibility)
* Threshold alerts at 80% / 100% (Observer + Strategy), streamed over SSE
* Strategy-driven reports discovered at runtime
* Idempotent recurring payments
"""


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    """Build the FastAPI app. ``settings`` and ``clock`` can be injected by tests."""
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if settings.auto_migrate:
            upgrade_database(settings.database_url)
        container = build_container(settings, clock)
        if settings.seed_demo_data:
            seed_demo_accounts(container)
        container.broadcaster.bind_loop(asyncio.get_running_loop())
        if settings.scheduler_enabled:
            container.scheduler.start()
        app.state.container = container
        try:
            yield
        finally:
            container.close()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=API_PREFIX)

    @app.get("/health", tags=["health"], summary="Liveness probe")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
