"""
Centralized error handling.

Per ARCHITECTURE.md §57 (ERROR HANDLING): the backend must provide
centralized error handling covering authentication/authorization failures,
validation errors, missing records, database errors, etc., and must never
expose stack traces to end users.

Per ARCHITECTURE.md §52 (API RESPONSE FORMAT): all error responses use

    {"success": false, "error": {"code": "...", "message": "..."}}

Routes raise `fastapi.HTTPException(status_code=..., detail={"code":...,
"message":...})` (see app/api/auth.py, app/core/dependencies.py for
examples) and these handlers translate that into the standard envelope.
Any HTTPException whose `detail` is a plain string (e.g. one raised by
FastAPI/Starlette internals rather than application code) still gets
wrapped, with a generic code.
"""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            body = _error_body(exc.detail["code"], exc.detail["message"])
        else:
            body = _error_body("HTTP_ERROR", str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Pydantic gives rich detail (field paths, messages) — safe to return,
        # since it describes the caller's own request, not internal state.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("VALIDATION_ERROR", "Request validation failed."),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        # Log the full exception server-side; never leak it to the client.
        logger.exception("Unhandled exception while processing request")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )
