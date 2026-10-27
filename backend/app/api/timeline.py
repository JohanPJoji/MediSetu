from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.consultation import Consultation
from app.models.prescription import Prescription
from app.models.referral import Referral
from app.models.document import Document
from app.services import patient_service

from app.core.dependencies import get_current_user, require_role

router = APIRouter()

def _success_response(data: dict):
    return {"success": True, "data": data, "message": None}

@router.get("/{patient_id}")
async def get_patient_timeline(
    patient_id: UUID,
    current_user: User = Depends(require_role([UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Forbidden"})
    elif current_user.role == UserRole.DOCTOR:
        assigned = await db.execute(
            select(Consultation.id).where(
                Consultation.patient_id == patient_id,
                Consultation.doctor_id == current_user.id,
            ).limit(1)
        )
        if assigned.scalar_one_or_none() is None:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Doctor is not authorized for this patient"})

    # Fetch consultations
    consultations_res = await db.execute(select(Consultation).where(Consultation.patient_id == patient_id))
    consultations = consultations_res.scalars().all()

    # Fetch prescriptions
    prescriptions_res = await db.execute(select(Prescription).where(Prescription.patient_id == patient_id))
    prescriptions = prescriptions_res.scalars().unique().all()

    # Fetch referrals
    referrals_res = await db.execute(select(Referral).where(Referral.patient_id == patient_id))
    referrals = referrals_res.scalars().unique().all()

    # Fetch documents
    documents_res = await db.execute(select(Document).where(Document.patient_id == patient_id))
    documents = documents_res.scalars().all()

    timeline = []
    
    for c in consultations:
        timeline.append({
            "type": "CONSULTATION",
            "id": str(c.id),
            "timestamp": c.created_at.isoformat(),
            "status": c.status,
            "doctor_id": str(c.doctor_id) if c.doctor_id else None
        })
        
    for p in prescriptions:
        timeline.append({
            "type": "PRESCRIPTION",
            "id": str(p.id),
            "timestamp": p.created_at.isoformat(),
            "status": p.status,
            "consultation_id": str(p.consultation_id)
        })
        
    for r in referrals:
        timeline.append({
            "type": "REFERRAL",
            "id": str(r.id),
            "timestamp": r.created_at.isoformat(),
            "status": r.status,
            "referring_doctor_id": str(r.referring_doctor_id) if r.referring_doctor_id else None,
            "referred_doctor_id": str(r.referred_doctor_id) if r.referred_doctor_id else None
        })
        
    for d in documents:
        timeline.append({
            "type": "DOCUMENT",
            "id": str(d.id),
            "timestamp": d.created_at.isoformat(),
            "file_name": d.file_name
        })
        
    # Sort timeline by timestamp descending
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return _success_response(timeline)
