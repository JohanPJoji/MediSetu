"""
Patient business logic.

Per ARCHITECTURE.md §9's repository structure and §89 (BACKEND BUSINESS
LOGIC — "Business logic must reside in services, not inside route
handlers"), this module holds Patient business logic separate from the API
route layer (app/api/patients.py) and the ORM layer (app/models/patient.py).

Decision: a Patient profile is created by the PATIENT-role user themself,
as an explicit "complete your profile" step AFTER registration/login — not
automatically at registration time. Registration (app/services/
auth_service.py) only creates the `User` (authentication identity);
REQUIREMENTS.md §4.1 lists "Identify/login to their profile" as a distinct
patient capability from account registration, and ARCHITECTURE.md §16's
intake workflow begins with "Identify patient" as its own step. Coupling
profile creation to registration would also force every DOCTOR/PHARMACY/
NURSE/ADMIN registration through Patient-profile logic for no reason. This
also matches how `docs/CURRENT_STATE.md`'s Phase 3 handoff described the
open decision, made explicit here rather than left implicit.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient, PatientSex
from app.services.audit_service import record_audit_event


class PatientAlreadyExistsError(Exception):
    """Raised when a User attempts to create a second Patient profile."""


class PatientNotFoundError(Exception):
    """Raised when a lookup by id/user_id finds no matching Patient."""


async def get_patient_by_id(db: AsyncSession, patient_id: uuid.UUID | str) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def get_patient_by_user_id(db: AsyncSession, user_id: uuid.UUID | str) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.user_id == user_id))
    return result.scalar_one_or_none()


async def create_patient(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    name: str,
    date_of_birth,
    sex: PatientSex,
    contact_information: str,
    preferred_language: str = "en",
) -> Patient:
    """
    Create the calling user's own Patient profile.

    Raises PatientAlreadyExistsError if this user_id already has a Patient
    profile (one profile per user in this phase — see module docstring).
    """
    existing = await get_patient_by_user_id(db, user_id)
    if existing is not None:
        raise PatientAlreadyExistsError(str(user_id))

    patient = Patient(
        user_id=user_id,
        name=name,
        date_of_birth=date_of_birth,
        sex=sex,
        contact_information=contact_information,
        preferred_language=preferred_language,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    await record_audit_event(db, action="PATIENT_CREATED", user_id=patient.user_id, resource_type="Patient", resource_id=patient.id)
    await db.commit()
    return patient


async def update_patient(db: AsyncSession, *, patient: Patient, updates: dict) -> Patient:
    """Apply a partial update (only keys present in `updates`, already
    filtered to exclude None values by the caller) to an existing Patient."""
    for field, value in updates.items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    await record_audit_event(db, action="PATIENT_UPDATED", user_id=patient.user_id, resource_type="Patient", resource_id=patient.id)
    await db.commit()
    return patient


async def list_patients(db: AsyncSession) -> list[Patient]:
    result = await db.execute(select(Patient).order_by(Patient.created_at))
    return list(result.scalars().all())
