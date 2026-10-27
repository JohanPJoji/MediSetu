"""
Centralized logging configuration.

Per ARCHITECTURE.md §58 (LOGGING):
- Logs must include timestamp, severity, module, and event.
- Logs must NEVER include passwords, JWT secrets, API keys, or unnecessary
  patient-sensitive information. Phase 1 has no such data paths yet, but
  the format is established now so later phases inherit safe defaults.
"""

import logging
import sys

from app.core.config import get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging() -> None:
    """Configure root logging handlers/format/level from settings. Idempotent."""
    settings = get_settings()

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Avoid duplicate handlers if called more than once (e.g. in tests + app startup).
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(handler)

    # Keep noisy third-party loggers at a reasonable level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
