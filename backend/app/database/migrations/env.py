"""
Alembic environment.

Wired to:
  - app.core.config.get_settings() for DATABASE_URL (never hard-coded here,
    per ARCHITECTURE.md §60/§100 — no secrets committed).
  - app.database.base.Base.metadata for autogenerate support, per
    ARCHITECTURE.md §91 (MIGRATIONS): "All schema changes must use Alembic."

Uses an async engine (asyncpg) run via `run_sync`, matching the async
SQLAlchemy setup used by the application itself (app/database/session.py).

Phase 1 defines no ORM models yet, so target_metadata is currently empty;
this migration environment is proven by generating and running the initial
(empty) migration. Future phases add models under app/models/ and import
them here so autogenerate can see them.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Ensure the application package is importable when Alembic is invoked
# from the backend/ directory (see alembic.ini: prepend_sys_path = .).
from app.core.config import get_settings
from app.database.base import Base

# Import model modules here as they are added in later phases so their
# tables register on Base.metadata before autogenerate runs.
from app.models.user import User
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry
from app.models.clinical_history import ClinicalHistory
from app.models.diagnosis import Diagnosis
from app.models.medicine import Medicine
from app.models.prescription import Prescription, PrescriptionItem
from app.models.referral import Referral
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.pharmacy_order import PharmacyOrder
from app.models.inventory_transaction import InventoryTransaction
from app.models.medicine_alert import MedicineAlert, AlternativeMedicine
from app.models.inventory_batch import InventoryBatch
from app.models.billing import Bill, BillItem, Payment
from app.models.laboratory import LabTest, LabOrder, LabResult

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the URL from alembic.ini with the one from application settings
# so there is a single source of truth for DATABASE_URL.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL without a live DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
