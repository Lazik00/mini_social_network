import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def error_payload(message: str, details: object | None = None) -> dict[str, object]:
    return {"success": False, "message": message, "details": details}


def serialize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    serialized_errors: list[dict[str, Any]] = []
    for error in errors:
        serialized_error = dict(error)
        ctx = serialized_error.get("ctx")
        if isinstance(ctx, dict):
            serialized_error["ctx"] = {key: str(value) for key, value in ctx.items()}
        serialized_errors.append(serialized_error)
    return serialized_errors


async def app_exception_handler(
    _request: Request,
    exc: AppException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.message, exc.details),
    )


async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(str(exc.detail)),
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_payload(
            "Validation error",
            serialize_validation_errors(exc.errors()),
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_payload("Internal server error"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
