"""
Patient model — the domain profile for a human receiving care.

Per ARCHITECTURE.md §13 (PATIENT MODEL) and the note on `app/models/user.py`
(ARCHITECTURE.md §10/§11): `User` is authentication identity only. `Patient`
is the separate domain entity holding clinical-profile fields, linked back
to `User` via `user_id`.

Field-by-field notes, since ARCHITECTURE.md §13 lists fields but leaves
exact types/nullability/constraints to implementation:

- `user_id`: FK to `users.id`, NOT NULL, UNIQUE — one Patient profile per
  User in this phase (a PATIENT-role user completes their own profile once;
  ARCHITECTURE.md doesn't describe multiple patient profiles per login, and
  REQUIREMENTS.md §4.1 describes the patient acting on "their profile",
  singular). A future phase that needs a caregiver managing multiple
  dependents' profiles would need to relax this uniqueness constraint
  deliberately, not by accident.
- `name`: kept as its own column rather than reading `User.full_name`.
  ARCHITECTURE.md §13 lists `name` as a Patient field explicitly, and in
  practice (kiosk walk-in intake, a family member registering on a
  patient's behalf) the clinical-record name is not guaranteed to match
  the login account's name. This does duplicate data in the common case
  where they match — a deliberate, documented tradeoff, not an oversight.
- `age` is intentionally NOT a stored column. ARCHITECTURE.md §13 says
  "Avoid unnecessary duplication of patient data" directly under a field
  list that includes both `date_of_birth` and `age`; storing both would
  require every consumer to keep them in sync or risk a stale age. `age`
  is instead derived at the API layer (see app/schemas/patient.py) from
  `date_of_birth`, which is the single source of truth.
- `sex`: modeled as a small Postgres enum (MALE/FEMALE/OTHER) rather than
  a free-text string, for consistency with `UserRole`'s enum pattern in
  `app/models/user.py` and to keep it queryable/constrained.
- `contact_information`: a single free-text field (phone or email), NOT
  NULL. ARCHITECTURE.md §13 lists it as one field, not separate
  phone/email columns; kept literal to that rather than inventing a
  sub-schema not asked for.
- `preferred_language`: free-text (e.g. "en", "hi", "ml") rather than an
  enum, per ARCHITECTURE.md §22 ("The architecture should allow additional
  Indian languages to be added without redesigning the entire system") —
  an enum would need a migration for every new language; a string does not.
- `abha_id`: nullable. Explicitly Phase 11 (EXTERNAL INTEGRATION) territory
  per ARCHITECTURE.md §46 — the column exists now (per §13's field list)
  but nothing in this phase populates or validates it.
"""

import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PatientSex(str, enum.Enum):
    """Sex options for the Patient profile. Kept small and explicit."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[PatientSex] = mapped_column(Enum(PatientSex, name="patient_sex"), nullable=False)
    contact_information: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    abha_id: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
