from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consultation import Consultation
from app.models.diagnosis import Diagnosis
from app.models.medicine import Medicine
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.user import User, UserRole
from app.models.pharmacy_order import PharmacyOrder, PharmacyOrderStatus
from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.schemas.doctor_workflow import DiagnosisCreate, PrescriptionCreate
from app.services.audit_service import record_audit_event


class MedicineInsufficientStockError(Exception):
    pass


class MedicineNotFoundError(Exception):
    pass


class InvalidPrescriptionError(Exception):
    pass


async def create_diagnosis(
    db: AsyncSession, consultation_id: UUID, doctor_id: UUID, diagnosis_in: DiagnosisCreate
) -> Diagnosis:
    consultation = await db.get(Consultation, consultation_id)
    if consultation is None:
        raise InvalidPrescriptionError("Consultation not found")
    if consultation.doctor_id != doctor_id:
        raise PermissionError("Doctor is not assigned to this consultation")

    db_diagnosis = Diagnosis(
        consultation_id=consultation_id,
        doctor_id=doctor_id,
        condition=diagnosis_in.condition.strip(),
        notes=diagnosis_in.notes,
    )
    db.add(db_diagnosis)
    await db.commit()
    await db.refresh(db_diagnosis)
    await record_audit_event(
        db, action="DIAGNOSIS_CREATED", user_id=doctor_id,
        resource_type="Diagnosis", resource_id=db_diagnosis.id,
        metadata={"consultation_id": str(consultation_id)}
    )
    await db.commit()
    return db_diagnosis


async def get_diagnoses_by_consultation(
    db: AsyncSession, consultation_id: UUID
) -> List[Diagnosis]:
    result = await db.execute(
        select(Diagnosis)
        .where(Diagnosis.consultation_id == consultation_id)
        .order_by(Diagnosis.created_at.desc())
    )
    return list(result.scalars().all())


async def create_prescription(
    db: AsyncSession, doctor_id: UUID, prescription_in: PrescriptionCreate
) -> Prescription:
    consultation = await db.get(Consultation, prescription_in.consultation_id)
    if consultation is None:
        raise InvalidPrescriptionError("Consultation not found")
    if consultation.doctor_id != doctor_id:
        raise PermissionError("Doctor is not assigned to this consultation")
    if consultation.patient_id != prescription_in.patient_id:
        raise InvalidPrescriptionError("patient_id does not match the consultation")

    if not prescription_in.items:
        raise InvalidPrescriptionError("Prescription must contain at least one medicine")
    if any(item.quantity <= 0 for item in prescription_in.items):
        raise InvalidPrescriptionError("Medicine quantities must be positive")

    # Lock each medicine row before checking/reserving stock.
    medicine_ids = list(dict.fromkeys(item.medicine_id for item in prescription_in.items))
    result = await db.execute(
        select(Medicine)
        .where(Medicine.id.in_(medicine_ids))
        .with_for_update()
    )
    medicines = {medicine.id: medicine for medicine in result.scalars().all()}

    if len(medicines) != len(medicine_ids):
        missing = next(mid for mid in medicine_ids if mid not in medicines)
        raise MedicineNotFoundError(f"Medicine {missing} not found")

    for item in prescription_in.items:
        medicine = medicines[item.medicine_id]
        available = medicine.current_stock - medicine.reserved_stock
        if available < item.quantity:
            raise MedicineInsufficientStockError(
                f"Not enough stock for {medicine.name}. "
                f"Requested: {item.quantity}, Available: {available}"
            )

    for item in prescription_in.items:
        medicines[item.medicine_id].reserved_stock += item.quantity

    db_prescription = Prescription(
        consultation_id=consultation.id,
        patient_id=consultation.patient_id,
        doctor_id=doctor_id,
        notes=prescription_in.notes,
        status=PrescriptionStatus.CONFIRMED,
    )
    db.add(db_prescription)
    await db.flush()

    for item in prescription_in.items:
        db.add(
            PrescriptionItem(
                prescription_id=db_prescription.id,
                medicine_id=item.medicine_id,
                dosage=item.dosage.strip(),
                frequency=item.frequency.strip(),
                duration=item.duration.strip(),
                quantity=item.quantity,
            )
        )

    await db.flush()

    order = PharmacyOrder(
        prescription_id=db_prescription.id,
        patient_id=consultation.patient_id,
        status=PharmacyOrderStatus.RESERVED,
    )
    db.add(order)
    await db.flush()

    for item in prescription_in.items:
        db.add(
            InventoryTransaction(
                medicine_id=item.medicine_id,
                prescription_id=db_prescription.id,
                order_id=order.id,
                transaction_type=InventoryTransactionType.STOCK_RESERVED,
                quantity=item.quantity,
            )
        )

    await db.commit()
    await record_audit_event(
        db, action="PRESCRIPTION_CONFIRMED", user_id=doctor_id,
        resource_type="Prescription", resource_id=db_prescription.id,
        metadata={"consultation_id": str(consultation.id)}
    )
    await db.commit()

    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.id == db_prescription.id)
    )
    return result.scalar_one()


async def list_prescriptions_by_patient(
    db: AsyncSession, patient_id: UUID
) -> List[Prescription]:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
    )
    return list(result.scalars().all())


async def list_all_prescriptions(db: AsyncSession) -> List[Prescription]:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .order_by(Prescription.created_at.desc())
    )
    return list(result.scalars().all())
