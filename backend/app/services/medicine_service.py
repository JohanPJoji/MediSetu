from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.medicine import Medicine
from app.schemas.medicine import MedicineCreate, MedicineUpdate
from app.services.audit_service import record_audit_event

class MedicineNotFoundError(Exception):
    pass

async def create_medicine(db: AsyncSession, medicine_in: MedicineCreate) -> Medicine:
    existing = await db.execute(select(Medicine).where(Medicine.name == medicine_in.name.strip()))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Medicine name already exists")
    db_medicine = Medicine(
        name=medicine_in.name.strip(),
        description=medicine_in.description,
        current_stock=medicine_in.current_stock,
        reserved_stock=0
    )
    db.add(db_medicine)
    await db.commit()
    await db.refresh(db_medicine)
    await record_audit_event(
        db, action="MEDICINE_CREATED", resource_type="Medicine",
        resource_id=db_medicine.id, metadata={"name": db_medicine.name}
    )
    await db.commit()
    return db_medicine

async def list_medicines(db: AsyncSession) -> List[Medicine]:
    result = await db.execute(select(Medicine).order_by(Medicine.name))
    return list(result.scalars().all())

async def get_medicine(db: AsyncSession, medicine_id: UUID) -> Optional[Medicine]:
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    return result.scalars().first()

async def update_medicine(db: AsyncSession, medicine_id: UUID, update_in: MedicineUpdate) -> Medicine:
    medicine = await get_medicine(db, medicine_id)
    if not medicine:
        raise MedicineNotFoundError()
        
    if update_in.name is not None:
        medicine.name = update_in.name
    if update_in.description is not None:
        medicine.description = update_in.description
    if update_in.current_stock is not None:
        if update_in.current_stock < medicine.reserved_stock:
            raise ValueError("current_stock cannot be lower than reserved_stock")
        medicine.current_stock = update_in.current_stock
        
    await db.commit()
    await db.refresh(medicine)
    await record_audit_event(
        db, action="MEDICINE_UPDATED", resource_type="Medicine",
        resource_id=medicine.id, metadata={"current_stock": medicine.current_stock}
    )
    await db.commit()
    return medicine
