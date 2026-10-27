from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.doctor_workflow import PrescriptionCreate, PrescriptionRead
from app.services import doctor_workflow_service, patient_service

from app.core.dependencies import get_current_user, require_role

router = APIRouter()

def _error_response(status_code: int, code: str, message: str):
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
        }
    )

def _success_response(data: dict):
    return {
        "success": True,
        "data": data,
        "message": None
    }

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_prescription(
    prescription_in: PrescriptionCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: AsyncSession = Depends(get_db)
):
    try:
        prescription = await doctor_workflow_service.create_prescription(db, current_user.id, prescription_in)
        return _success_response(PrescriptionRead.model_validate(prescription).model_dump(mode="json"))
    except doctor_workflow_service.MedicineNotFoundError as e:
        _error_response(404, "MEDICINE_NOT_FOUND", str(e))
    except doctor_workflow_service.MedicineInsufficientStockError as e:
        _error_response(400, "INSUFFICIENT_STOCK", str(e))
    except PermissionError:
        _error_response(403, "FORBIDDEN", "Doctor is not authorized for this consultation")
    except doctor_workflow_service.InvalidPrescriptionError:
        _error_response(400, "INVALID_PRESCRIPTION", "The prescription data is invalid")
    except Exception:
        _error_response(500, "INTERNAL_ERROR", "Unable to create prescription")

@router.get("")
async def list_prescriptions(
    current_user: User = Depends(require_role([UserRole.PATIENT, UserRole.DOCTOR, UserRole.PHARMACY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        if not patient:
            return _success_response([])
        prescriptions = await doctor_workflow_service.list_prescriptions_by_patient(db, patient.id)
    else:
        prescriptions = await doctor_workflow_service.list_all_prescriptions(db)
        
    return _success_response([PrescriptionRead.model_validate(p).model_dump(mode="json") for p in prescriptions])
