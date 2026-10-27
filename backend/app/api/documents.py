from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.consultation import Consultation
from app.models.user import User, UserRole
from app.schemas.document import DocumentCreate, DocumentRead
from app.services import document_service, patient_service
from app.services.ocr_service import ocr_service

router = APIRouter()


def _error_response(status_code: int, code: str, message: str):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _success_response(data):
    return {"success": True, "data": data, "message": None}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_document(
    document_in: DocumentCreate,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        if not patient or patient.id != document_in.patient_id:
            _error_response(403, "FORBIDDEN", "Forbidden")
    elif current_user.role == UserRole.DOCTOR:
        if document_in.consultation_id is None:
            _error_response(400, "CONSULTATION_REQUIRED", "Doctors must attach documents to a consultation")
        consultation = await db.get(Consultation, document_in.consultation_id)
        if (
            consultation is None
            or consultation.patient_id != document_in.patient_id
            or consultation.doctor_id != current_user.id
        ):
            _error_response(403, "FORBIDDEN", "Doctor is not authorized for this patient/consultation")

    document = await document_service.create_document(db, document_in)
    return _success_response(DocumentRead.model_validate(document).model_dump(mode="json"))




@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    patient_id: UUID | None = None,
    consultation_id: UUID | None = None,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document and run the configured OCR abstraction."""
    if patient_id is None:
        _error_response(400, "PATIENT_REQUIRED", "patient_id is required")

    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        if not patient or patient.id != patient_id:
            _error_response(403, "FORBIDDEN", "Forbidden")
    elif current_user.role == UserRole.DOCTOR:
        if consultation_id is None:
            _error_response(400, "CONSULTATION_REQUIRED", "Doctors must attach documents to a consultation")
        consultation = await db.get(Consultation, consultation_id)
        if not consultation or consultation.patient_id != patient_id or consultation.doctor_id != current_user.id:
            _error_response(403, "FORBIDDEN", "Doctor is not authorized for this patient/consultation")

    content = await file.read()
    if not content:
        _error_response(400, "EMPTY_FILE", "Uploaded file is empty")

    try:
        extracted_text = await ocr_service.extract_text(
            file.filename or "document",
            content,
            file.content_type or "application/octet-stream",
        )
    except Exception as exc:
        _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "OCR_UNAVAILABLE", str(exc))

    document = await document_service.create_document(
        db,
        DocumentCreate(
            patient_id=patient_id,
            consultation_id=consultation_id,
            file_name=file.filename or "document",
            file_type=file.content_type or "application/octet-stream",
            file_url="local://uploaded-document",
            extracted_text=extracted_text,
        ),
    )
    return _success_response(DocumentRead.model_validate(document).model_dump(mode="json"))


@router.get("")
async def list_documents(
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        documents = await document_service.list_documents(db, patient_id=patient.id) if patient else []
    elif current_user.role == UserRole.DOCTOR:
        documents = await document_service.list_documents_for_doctor(db, current_user.id)
    else:
        documents = await document_service.list_documents(db)

    return _success_response([DocumentRead.model_validate(d).model_dump(mode="json") for d in documents])
