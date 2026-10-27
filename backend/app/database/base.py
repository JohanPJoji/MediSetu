"""
SQLAlchemy declarative base.

Per ARCHITECTURE.md §90 (DATABASE ACCESS): SQLAlchemy is the primary
ORM/data-access layer for the whole project.

All future ORM models (Phase 2+: User, Patient, Doctor, Consultation, ...)
must import and inherit from `Base` defined here so that a single
`Base.metadata` drives Alembic autogeneration (see alembic/env.py).

No models are defined in Phase 1 — this file exists purely to establish
the shared metadata object ahead of Phase 2.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models in the project."""

    pass
