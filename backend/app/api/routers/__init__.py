"""Versioned API routers."""

from fastapi import APIRouter

from app.api.routers import (
    admin,
    alerts,
    auth,
    budgets,
    categories,
    categorize,
    dashboard,
    recurring,
    reports,
    rules,
    transactions,
)

api_router = APIRouter()
for module in (
    auth,
    dashboard,
    transactions,
    categories,
    budgets,
    rules,
    categorize,
    recurring,
    reports,
    alerts,
    admin,
):
    api_router.include_router(module.router)
