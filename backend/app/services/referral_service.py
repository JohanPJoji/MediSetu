from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referral import Referral, ReferralStatus
from app.schemas.referral import ReferralCreate, ReferralUpdate
from app.services.audit_service import record_audit_event


class ReferralNotFoundError(Exception):
    pass


class InvalidReferralError(Exception):
    pass


async def create_referral(
    db: AsyncSession, referring_doctor_id: UUID, referral_in: ReferralCreate
) -> Referral:
    if referral_in.referred_doctor_id == referring_doctor_id:
        raise InvalidReferralError("A doctor cannot refer a case to themselves")

    db_referral = Referral(
        consultation_id=referral_in.consultation_id,
        patient_id=referral_in.patient_id,
        referring_doctor_id=referring_doctor_id,
        referred_doctor_id=referral_in.referred_doctor_id,
        reason=referral_in.reason.strip(),
        notes=referral_in.notes,
    )
    db.add(db_referral)
    await db.commit()
    await db.refresh(db_referral)
    await record_audit_event(
        db, action="REFERRAL_CREATED", user_id=referring_doctor_id,
        resource_type="Referral", resource_id=db_referral.id
    )
    await db.commit()
    return db_referral


async def list_referrals(
    db: AsyncSession,
    doctor_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
) -> List[Referral]:
    query = select(Referral).order_by(Referral.created_at.desc())
    if doctor_id is not None:
        query = query.where(
            (Referral.referring_doctor_id == doctor_id)
            | (Referral.referred_doctor_id == doctor_id)
        )
    if patient_id is not None:
        query = query.where(Referral.patient_id == patient_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_referral_by_id(db: AsyncSession, referral_id: UUID) -> Optional[Referral]:
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    return result.scalar_one_or_none()


async def update_referral(
    db: AsyncSession,
    referral_id: UUID,
    update_in: ReferralUpdate,
    acting_doctor_id: UUID | None = None,
    is_admin: bool = False,
) -> Referral:
    referral = await get_referral_by_id(db, referral_id)
    if referral is None:
        raise ReferralNotFoundError()

    if not is_admin:
        if acting_doctor_id not in (referral.referring_doctor_id, referral.referred_doctor_id):
            raise PermissionError("Doctor is not part of this referral")
        if acting_doctor_id == referral.referring_doctor_id and update_in.status != ReferralStatus.CANCELLED:
            raise PermissionError("Only the receiving doctor can accept/reject/complete a referral")

    valid_transitions = {
        ReferralStatus.PENDING: {ReferralStatus.ACCEPTED, ReferralStatus.REJECTED, ReferralStatus.CANCELLED},
        ReferralStatus.ACCEPTED: {ReferralStatus.COMPLETED},
        ReferralStatus.REJECTED: set(),
        ReferralStatus.COMPLETED: set(),
        ReferralStatus.CANCELLED: set(),
    }
    if update_in.status not in valid_transitions[referral.status]:
        raise InvalidReferralError(
            f"Cannot transition from {referral.status.value} to {update_in.status.value}"
        )

    referral.status = update_in.status
    if update_in.notes is not None:
        referral.notes = update_in.notes

    await db.commit()
    await db.refresh(referral)
    await record_audit_event(
        db, action="REFERRAL_STATUS_CHANGED",
        resource_type="Referral", resource_id=referral.id,
        metadata={"status": referral.status.value}
    )
    await db.commit()
    return referral
