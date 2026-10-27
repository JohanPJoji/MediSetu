from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical_history import ClinicalHistory
from app.schemas.clinical_history import ClinicalHistoryCreate, ClinicalHistoryUpdate
from app.services.audit_service import record_audit_event


class ClinicalHistoryNotFoundError(Exception):
    pass


class ClinicalHistoryAlreadyExistsError(Exception):
    pass


async def get_clinical_history_by_consultation_id(
    db: AsyncSession, consultation_id: UUID
) -> Optional[ClinicalHistory]:
    result = await db.execute(
        select(ClinicalHistory).where(ClinicalHistory.consultation_id == consultation_id)
    )
    return result.scalar_one_or_none()


async def get_clinical_history_by_id(
    db: AsyncSession, history_id: UUID
) -> Optional[ClinicalHistory]:
    result = await db.execute(
        select(ClinicalHistory).where(ClinicalHistory.id == history_id)
    )
    return result.scalar_one_or_none()


async def create_clinical_history(
    db: AsyncSession, consultation_id: UUID, history_in: ClinicalHistoryCreate
) -> ClinicalHistory:
    existing = await get_clinical_history_by_consultation_id(db, consultation_id)
    if existing is not None:
        raise ClinicalHistoryAlreadyExistsError()

    db_history = ClinicalHistory(
        consultation_id=consultation_id,
        **history_in.model_dump(exclude_unset=True),
    )
    db.add(db_history)
    await db.commit()
    await db.refresh(db_history)
    await record_audit_event(
        db, action="CLINICAL_HISTORY_CREATED", resource_type="ClinicalHistory",
        resource_id=db_history.id, metadata={"consultation_id": str(consultation_id)}
    )
    await db.commit()
    return db_history


async def update_clinical_history(
    db: AsyncSession, consultation_id: UUID, history_update: ClinicalHistoryUpdate
) -> ClinicalHistory:
    db_history = await get_clinical_history_by_consultation_id(db, consultation_id)
    if db_history is None:
        raise ClinicalHistoryNotFoundError()

    for field, value in history_update.model_dump(exclude_unset=True).items():
        setattr(db_history, field, value)

    await db.commit()
    await db.refresh(db_history)
    await record_audit_event(
        db, action="CLINICAL_HISTORY_UPDATED", resource_type="ClinicalHistory",
        resource_id=db_history.id, metadata={"consultation_id": str(consultation_id)}
    )
    await db.commit()
    return db_history
