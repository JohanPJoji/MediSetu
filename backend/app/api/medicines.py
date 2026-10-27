from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.medicine import MedicineCreate, MedicineRead, MedicineUpdate
from app.services import medicine_service

from app.core.dependencies import get_current_user, require_role

router = APIRouter()

def _error_response(status_code: int, code: str, message: str):
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message}
    )

def _success_response(data: dict):
    return {"success": True, "data": data, "message": None}

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_medicine(
    medicine_in: MedicineCreate,
    current_user: User = Depends(require_role([UserRole.PHARMACY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    try:
        medicine = await medicine_service.create_medicine(db, medicine_in)
        return _success_response(MedicineRead.model_validate(medicine).model_dump(mode="json"))
    except ValueError as exc:
        _error_response(409, "MEDICINE_CONFLICT", str(exc))
    except Exception:
        _error_response(500, "INTERNAL_ERROR", "Unable to create medicine")

@router.get("")
async def list_medicines(
    current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.PHARMACY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    medicines = await medicine_service.list_medicines(db)
    return _success_response([MedicineRead.model_validate(m).model_dump(mode="json") for m in medicines])

@router.patch("/{medicine_id}")
async def update_medicine(
    medicine_id: UUID,
    update_in: MedicineUpdate,
    current_user: User = Depends(require_role([UserRole.PHARMACY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    try:
        medicine = await medicine_service.update_medicine(db, medicine_id, update_in)
        return _success_response(MedicineRead.model_validate(medicine).model_dump(mode="json"))
    except medicine_service.MedicineNotFoundError:
        _error_response(404, "MEDICINE_NOT_FOUND", "Medicine not found")
    except ValueError as exc:
        _error_response(409, "MEDICINE_CONFLICT", str(exc))
