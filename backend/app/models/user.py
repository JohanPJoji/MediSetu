"""
User model — the authentication identity for every human in the system.

Per ARCHITECTURE.md §10 (USER ROLES) and §11 (AUTHENTICATION): every human
actor (patient, doctor, pharmacy staff, nurse, admin) authenticates as a
`User` with exactly one `role`. Role-specific profile data (e.g. a
patient's date of birth, a doctor's specialization — ARCHITECTURE.md §13,
§14) is deliberately NOT stored here; those become separate `Patient` /
`Doctor` tables in Phase 3/4, each with a `user_id` foreign key back to
this table, per ARCHITECTURE.md §13/§14's explicit field lists.

Passwords are never stored in plaintext (ARCHITECTURE.md §11) — only
`hashed_password` (bcrypt, via app.core.security) is persisted.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserRole(str, enum.Enum):
    """The five roles defined in ARCHITECTURE.md §10."""

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    PHARMACY = "PHARMACY"
    NURSE = "NURSE"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
