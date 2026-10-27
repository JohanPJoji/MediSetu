"""
Patient API routes.

Per ARCHITECTURE.md §51: mounted under /api/patients.
Per ARCHITECTURE.md §12 (ROLE-BASED ACCESS CONTROL):

  Patient can: access their own profile ... view permitted personal records
  Patient cannot: access another patient

  Doctor can: access authorized patient cases ... review previous records

RBAC decisions made explicit here (documented, not guessed):

- A PATIENT-role user manages their OWN profile only, via the `/me`
  routes (create/read/update). There is deliberately no generic
  `PATCH /api/patients/{id}` for patients — a patient can never even
  construct a request that targets someone else's record, which is a
  stronger guarantee than an ownership check that could be gotten wrong.
- `GET /api/patients/{patient_id}` is for clinical staff (DOCTOR, NURSE)
  and ADMIN, NOT for PATIENT — this is what makes "cannot access another
  patient" true (a PATIENT-role token gets 403 from this route
  regardless of which id is requested, per `require_role` in
  app.core.dependencies).
- ARCHITECTURE.md §12 says a Doctor may access "authorized" patient
  cases — but Phase 3 has no Consultation/assignment model yet (that's
  Phase 4/6, ARCHITECTURE.md §102). Restricting which doctor may view
  which patient therefore cannot be implemented correctly yet. Rather
  than fake an authorization check with no real basis (e.g. "any doctor
  who has ever ..."), this phase deliberately allows any DOCTOR or NURSE
  to view any patient profile, and explicitly defers per-case
  authorization to Phase 4/6. This is flagged again in
  docs/CURRENT_STATE.md so it isn't mistaken for a finished access model.
- `GET /api/patients` (list all) is ADMIN-only, mirroring the existing
  `GET /api/users` pattern in app/api/users.py.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.consultation import Consultation

from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.services.patient_service import (
    PatientAlreadyExistsError,
    create_patient,
    get_patient_by_id,
    get_patient_by_user_id,
    list_patients,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["patients"])


def _serialize(patient) -> dict:
    read = PatientRead.model_validate(patient)
    return read.model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_own_patient_profile(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.PATIENT)),
) -> dict:
    """Create the caller's own Patient profile. PATIENT role only."""
    try:
        patient = await create_patient(
            db,
            user_id=user.id,
            name=body.name,
            date_of_birth=body.date_of_birth,
            sex=body.sex,
            contact_information=body.contact_information,
            preferred_language=body.preferred_language,
        )
    except PatientAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PATIENT_PROFILE_ALREADY_EXISTS",
                "message": "A patient profile already exists for this account.",
            },
        )

    return {"success": True, "data": _serialize(patient), "message": None}


@router.get("/me")
async def read_own_patient_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.PATIENT)),
) -> dict:
    """Return the caller's own Patient profile. PATIENT role only."""
    patient = await get_patient_by_user_id(db, user.id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PATIENT_PROFILE_NOT_FOUND",
                "message": "No patient profile has been created for this account yet.",
            },
        )

    return {"success": True, "data": _serialize(patient), "message": None}


@router.patch("/me")
async def update_own_patient_profile(
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.PATIENT)),
) -> dict:
    """Partially update the caller's own Patient profile. PATIENT role only."""
    patient = await get_patient_by_user_id(db, user.id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PATIENT_PROFILE_NOT_FOUND",
                "message": "No patient profile has been created for this account yet.",
            },
        )

    updates = body.model_dump(exclude_none=True)
    patient = await update_patient(db, patient=patient, updates=updates)
    return {"success": True, "data": _serialize(patient), "message": None}


@router.get("")
async def list_all_patients(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    """List all patients. ADMIN role only, per ARCHITECTURE.md §12."""
    patients = await list_patients(db)
    return {"success": True, "data": [_serialize(p) for p in patients], "message": None}


@router.get("/{patient_id}")
async def read_patient_by_id(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_role(UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
) -> dict:
    """
    Look up a patient by id. Restricted to DOCTOR, NURSE, and ADMIN — NOT
    PATIENT (see module docstring: this is what enforces "a patient cannot
    access another patient" from ARCHITECTURE.md §12, since no PATIENT-role
    token can ever pass `require_role` here, regardless of id).
    """
    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PATIENT_NOT_FOUND", "message": "No patient found with this id."},
        )

    if _staff.role == UserRole.DOCTOR:
        assigned = await db.execute(
            select(Consultation.id).where(
                Consultation.patient_id == patient_id,
                Consultation.doctor_id == _staff.id,
            ).limit(1)
        )
        if assigned.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Doctor is not authorized for this patient."},
            )

    return {"success": True, "data": _serialize(patient), "message": None}
