from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.referral import ReferralCreate, ReferralRead, ReferralUpdate
from app.services import patient_service, referral_service

router = APIRouter()


def _error_response(status_code: int, code: str, message: str):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _success_response(data):
    return {"success": True, "data": data, "message": None}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_referral(
    referral_in: ReferralCreate,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    try:
        referral = await referral_service.create_referral(db, current_user.id, referral_in)
    except referral_service.InvalidReferralError as exc:
        _error_response(400, "INVALID_REFERRAL", str(exc))
    return _success_response(ReferralRead.model_validate(referral).model_dump(mode="json"))


@router.get("")
async def list_referrals(
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        referrals = await referral_service.list_referrals(db, patient_id=patient.id) if patient else []
    elif current_user.role == UserRole.DOCTOR:
        referrals = await referral_service.list_referrals(db, doctor_id=current_user.id)
    else:
        referrals = await referral_service.list_referrals(db)

    return _success_response([ReferralRead.model_validate(r).model_dump(mode="json") for r in referrals])


@router.patch("/{referral_id}")
async def update_referral(
    referral_id: UUID,
    update_in: ReferralUpdate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    try:
        referral = await referral_service.update_referral(
            db,
            referral_id,
            update_in,
            acting_doctor_id=current_user.id if current_user.role == UserRole.DOCTOR else None,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except referral_service.ReferralNotFoundError:
        _error_response(404, "REFERRAL_NOT_FOUND", "Referral not found")
    except PermissionError as exc:
        _error_response(403, "FORBIDDEN", str(exc))
    except referral_service.InvalidReferralError as exc:
        _error_response(400, "INVALID_REFERRAL", str(exc))
    return _success_response(ReferralRead.model_validate(referral).model_dump(mode="json"))
