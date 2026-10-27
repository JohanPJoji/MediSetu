from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.models.medicine import Medicine
from app.models.pharmacy_order import PharmacyOrder, PharmacyOrderStatus
from app.models.prescription import Prescription, PrescriptionStatus
from app.models.user import User, UserRole
from app.schemas.pharmacy import PharmacyOrderRead, PharmacyOrderStatusUpdate
from app.services.audit_service import record_audit_event

router = APIRouter()

ALLOWED_TRANSITIONS = {
    PharmacyOrderStatus.RESERVED: {PharmacyOrderStatus.PREPARING, PharmacyOrderStatus.CANCELLED},
    PharmacyOrderStatus.PREPARING: {PharmacyOrderStatus.READY_FOR_PICKUP, PharmacyOrderStatus.CANCELLED},
    PharmacyOrderStatus.READY_FOR_PICKUP: {PharmacyOrderStatus.DISPENSED, PharmacyOrderStatus.CANCELLED},
    PharmacyOrderStatus.PENDING: {PharmacyOrderStatus.RESERVED, PharmacyOrderStatus.CANCELLED},
    PharmacyOrderStatus.DISPENSED: set(),
    PharmacyOrderStatus.CANCELLED: set(),
    PharmacyOrderStatus.EXPIRED: set(),
}


def _error_response(status_code: int, code: str, message: str):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _success_response(data):
    return {"success": True, "data": data, "message": None}


@router.get("/orders")
async def list_pharmacy_orders(
    status: PharmacyOrderStatus | None = None,
    current_user: User = Depends(require_role(UserRole.PHARMACY, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    query = select(PharmacyOrder).order_by(PharmacyOrder.created_at.desc())
    if status is not None:
        query = query.where(PharmacyOrder.status == status)
    result = await db.execute(query)
    orders = result.scalars().all()
    return _success_response([PharmacyOrderRead.model_validate(o).model_dump(mode="json") for o in orders])


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    status_update: PharmacyOrderStatusUpdate,
    current_user: User = Depends(require_role(UserRole.PHARMACY, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PharmacyOrder)
        .options(selectinload(PharmacyOrder.prescription).selectinload(Prescription.items))
        .where(PharmacyOrder.id == order_id)
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        _error_response(404, "ORDER_NOT_FOUND", "Pharmacy order not found")

    old_status = order.status
    new_status = status_update.status
    if new_status == old_status:
        return _success_response(PharmacyOrderRead.model_validate(order).model_dump(mode="json"))

    if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
        _error_response(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_ORDER_TRANSITION",
            f"Cannot transition order from {old_status.value} to {new_status.value}",
        )

    prescription = order.prescription
    if prescription is None:
        _error_response(409, "ORDER_INVALID", "Pharmacy order has no prescription")

    medicine_ids = [item.medicine_id for item in prescription.items]
    med_result = await db.execute(
        select(Medicine).where(Medicine.id.in_(medicine_ids)).with_for_update()
    )
    medicines = {m.id: m for m in med_result.scalars().all()}

    if new_status == PharmacyOrderStatus.DISPENSED:
        for item in prescription.items:
            medicine = medicines.get(item.medicine_id)
            if medicine is None or medicine.reserved_stock < item.quantity or medicine.current_stock < item.quantity:
                _error_response(409, "STOCK_INCONSISTENT", "Inventory is inconsistent for this order")
            medicine.reserved_stock -= item.quantity
            medicine.current_stock -= item.quantity
            db.add(
                InventoryTransaction(
                    medicine_id=item.medicine_id,
                    prescription_id=prescription.id,
                    order_id=order.id,
                    transaction_type=InventoryTransactionType.STOCK_DISPENSED,
                    quantity=item.quantity,
                )
            )
        prescription.status = PrescriptionStatus.DISPENSED

    elif new_status == PharmacyOrderStatus.CANCELLED:
        for item in prescription.items:
            medicine = medicines.get(item.medicine_id)
            if medicine is None or medicine.reserved_stock < item.quantity:
                _error_response(409, "STOCK_INCONSISTENT", "Reserved inventory is inconsistent for this order")
            medicine.reserved_stock -= item.quantity
            db.add(
                InventoryTransaction(
                    medicine_id=item.medicine_id,
                    prescription_id=prescription.id,
                    order_id=order.id,
                    transaction_type=InventoryTransactionType.STOCK_RELEASED,
                    quantity=item.quantity,
                )
            )
        prescription.status = PrescriptionStatus.CANCELLED

    elif new_status == PharmacyOrderStatus.PREPARING:
        prescription.status = PrescriptionStatus.PREPARING
    elif new_status == PharmacyOrderStatus.READY_FOR_PICKUP:
        prescription.status = PrescriptionStatus.READY

    order.status = new_status
    await db.flush()
    await record_audit_event(
        db,
        action="PHARMACY_ORDER_STATUS_CHANGED",
        user_id=current_user.id,
        resource_type="PharmacyOrder",
        resource_id=order.id,
        metadata={"status": order.status.value},
    )
    await db.commit()
    await db.refresh(order)
    return _success_response(PharmacyOrderRead.model_validate(order).model_dump(mode="json"))
