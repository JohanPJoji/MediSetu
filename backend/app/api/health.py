"""
Health check endpoint.

Per ARCHITECTURE.md §102 (Phase 1 — Foundation), the definition of done
requires a health check that passes. Per §52 (API RESPONSE FORMAT), all
responses use the standard {"success", "data", "message"} envelope, and
per §57, failures must not leak internal implementation details.
"""

import logging

from fastapi import APIRouter

from app.database.session import check_database_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """
    Report application and database health.

    Returns 200 with database status "ok" or "unavailable" — the endpoint
    itself always responds successfully as long as the FastAPI process is
    running; database reachability is reported as data, not as an HTTP
    error, so monitoring/demo tooling gets a clear signal either way.
    """
    db_status = "ok"
    try:
        await check_database_connection()
    except Exception:
        logger.exception("Health check: database connectivity failed")
        db_status = "unavailable"

    return {
        "success": True,
        "data": {
            "status": "ok",
            "database": db_status,
        },
        "message": None,
    }
