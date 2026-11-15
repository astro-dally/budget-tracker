"""Global exception handlers producing one consistent error envelope.

Every error looks like ``{"error": {"code", "message", "details": [...]}}``,
so the frontend's API client handles failures in exactly one place.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas import ErrorBody, ErrorDetail, ErrorOut
from app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
    TooManyAttemptsError,
)

logger = logging.getLogger(__name__)

HTTP_422 = 422  # named locally: Starlette renamed its constant across versions


def error_response(
    status_code: int, code: str, message: str, details: list[ErrorDetail] | None = None
) -> JSONResponse:
    """Build the standard error JSON."""
    body = ErrorOut(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def _unauthenticated(_: Request, exc: Exception) -> JSONResponse:
    response = error_response(status.HTTP_401_UNAUTHORIZED, "unauthenticated", str(exc))
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


async def _forbidden(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_403_FORBIDDEN, "forbidden", str(exc))


async def _too_many(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts", str(exc))


async def _not_found(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_404_NOT_FOUND, "not_found", str(exc))


async def _conflict(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_409_CONFLICT, "conflict", str(exc))


async def _domain_validation(_: Request, exc: Exception) -> JSONResponse:
    return error_response(HTTP_422, "validation_error", str(exc))


async def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_400_BAD_REQUEST, "domain_error", str(exc))


async def _request_validation(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"] if part != "body"),
            message=str(error["msg"]),
        )
        for error in exc.errors()
    ]
    return error_response(
        HTTP_422,
        "validation_error",
        "The request contains invalid fields",
        details,
    )


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return error_response(exc.status_code, "http_error", str(exc.detail))


async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Something went wrong on the server",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install every handler on ``app``. More specific exception classes win."""
    app.add_exception_handler(AuthenticationError, _unauthenticated)
    app.add_exception_handler(PermissionDeniedError, _forbidden)
    app.add_exception_handler(TooManyAttemptsError, _too_many)
    app.add_exception_handler(NotFoundError, _not_found)
    app.add_exception_handler(ConflictError, _conflict)
    app.add_exception_handler(DomainValidationError, _domain_validation)
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _request_validation)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected)
