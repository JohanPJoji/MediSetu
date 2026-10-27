from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation, ConsultationStatus
from app.models.user import User, UserRole
from app.schemas.consultation import ConsultationCreate
from app.services.audit_service import record_audit_event


class ConsultationNotFoundError(Exception):
    pass


class InvalidStateTransitionError(Exception):
    pass


class InvalidDoctorAssignmentError(Exception):
    pass


VALID_TRANSITIONS = {
    ConsultationStatus.CREATED: {ConsultationStatus.IN_PROGRESS, ConsultationStatus.CANCELLED},
    ConsultationStatus.IN_PROGRESS: {ConsultationStatus.AI_PROCESSING, ConsultationStatus.CANCELLED},
    ConsultationStatus.AI_PROCESSING: {ConsultationStatus.UNDER_REVIEW, ConsultationStatus.CANCELLED},
    ConsultationStatus.UNDER_REVIEW: {ConsultationStatus.APPROVED, ConsultationStatus.CANCELLED},
    ConsultationStatus.APPROVED: {ConsultationStatus.COMPLETED, ConsultationStatus.CANCELLED},
    ConsultationStatus.COMPLETED: set(),
    ConsultationStatus.CANCELLED: set(),
}


async def get_consultation_by_id(
    db: AsyncSession, consultation_id: UUID
) -> Optional[Consultation]:
    result = await db.execute(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    return result.scalar_one_or_none()


async def create_consultation(
    db: AsyncSession, consultation_in: ConsultationCreate
) -> Consultation:
    if consultation_in.doctor_id is not None:
        result = await db.execute(
            select(User).where(
                User.id == consultation_in.doctor_id,
                User.role == UserRole.DOCTOR,
                User.is_active.is_(True),
            )
        )
        if result.scalar_one_or_none() is None:
            raise InvalidDoctorAssignmentError("doctor_id must reference an active doctor")

    db_consultation = Consultation(
        patient_id=consultation_in.patient_id,
        doctor_id=consultation_in.doctor_id,
        status=ConsultationStatus.CREATED,
    )
    db.add(db_consultation)
    await db.commit()
    await db.refresh(db_consultation)
    await record_audit_event(
        db, action="CONSULTATION_CREATED", resource_type="Consultation",
        resource_id=db_consultation.id, metadata={"patient_id": str(db_consultation.patient_id)}
    )
    await db.commit()
    return db_consultation


async def list_consultations(
    db: AsyncSession,
    patient_id: Optional[UUID] = None,
    doctor_id: Optional[UUID] = None,
) -> List[Consultation]:
    query = select(Consultation).order_by(Consultation.created_at.desc())
    if patient_id is not None:
        query = query.where(Consultation.patient_id == patient_id)
    if doctor_id is not None:
        query = query.where(Consultation.doctor_id == doctor_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_consultation_status(
    db: AsyncSession,
    consultation_id: UUID,
    new_status: ConsultationStatus,
) -> Consultation:
    consultation = await get_consultation_by_id(db, consultation_id)
    if consultation is None:
        raise ConsultationNotFoundError()

    if new_status not in VALID_TRANSITIONS[consultation.status]:
        raise InvalidStateTransitionError(
            f"Cannot transition from {consultation.status.value} to {new_status.value}"
        )

    now = datetime.now(timezone.utc)
    consultation.status = new_status

    if new_status == ConsultationStatus.IN_PROGRESS and consultation.started_at is None:
        consultation.started_at = now
    if new_status in {ConsultationStatus.COMPLETED, ConsultationStatus.CANCELLED}:
        consultation.completed_at = now

    await db.commit()
    await db.refresh(consultation)
    await record_audit_event(
        db, action="CONSULTATION_STATUS_CHANGED", resource_type="Consultation",
        resource_id=consultation.id, metadata={"status": consultation.status.value}
    )
    await db.commit()
    return consultation


async def assign_doctor(
    db: AsyncSession, consultation_id: UUID, doctor_id: UUID
) -> Consultation:
    consultation = await get_consultation_by_id(db, consultation_id)
    if consultation is None:
        raise ConsultationNotFoundError()

    result = await db.execute(
        select(User).where(
            User.id == doctor_id,
            User.role == UserRole.DOCTOR,
            User.is_active.is_(True),
        )
    )
    if result.scalar_one_or_none() is None:
        raise InvalidDoctorAssignmentError("doctor_id must reference an active doctor")

    consultation.doctor_id = doctor_id
    await db.commit()
    await db.refresh(consultation)
    await record_audit_event(
        db, action="CONSULTATION_ASSIGNED", resource_type="Consultation",
        resource_id=consultation.id, metadata={"doctor_id": str(doctor_id)}
    )
    await db.commit()
    return consultation
