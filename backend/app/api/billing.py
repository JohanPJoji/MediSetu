from datetime import datetime, timezone
from decimal import Decimal
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.billing import Bill, BillItem, Payment
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.billing import BillCreate, BillRead, BillStatusUpdate, PaymentCreate, PaymentRead

router = APIRouter()
def ok(data): return {"success": True, "data": data, "message": None}
def err(code, message, status_code): raise HTTPException(status_code=status_code, detail={"code": code, "message": message})

async def _read_bill(db: AsyncSession, bill: Bill):
    await db.refresh(bill, attribute_names=["items"])
    return BillRead.model_validate(bill).model_dump(mode="json")

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_bill(body: BillCreate, _: User = Depends(require_role([UserRole.ADMIN, UserRole.NURSE])), db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, body.patient_id)
    if not patient: err("PATIENT_NOT_FOUND", "Patient not found.", 404)
    subtotal = sum(Decimal(str(item.quantity)) * Decimal(str(item.unit_price)) for item in body.items)
    total = subtotal - Decimal(str(body.discount)) + Decimal(str(body.tax))
    if total < 0: err("INVALID_TOTAL", "Bill total cannot be negative.", 422)
    bill = Bill(bill_number=f"B-{uuid.uuid4().hex[:10].upper()}", patient_id=body.patient_id, consultation_id=body.consultation_id, subtotal=subtotal, discount=body.discount, tax=body.tax, total_amount=total)
    db.add(bill); await db.flush()
    for item in body.items:
        db.add(BillItem(bill_id=bill.id, item_type=item.item_type, item_reference_id=item.item_reference_id, description=item.description, quantity=item.quantity, unit_price=item.unit_price, total_price=Decimal(str(item.quantity)) * Decimal(str(item.unit_price))))
    await db.commit(); await db.refresh(bill); return ok(await _read_bill(db, bill))

@router.get("")
async def list_bills(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Bill).order_by(Bill.created_at.desc())
    if current.role == UserRole.PATIENT:
        patient = await db.scalar(select(Patient).where(Patient.user_id == current.id))
        q = q.where(Bill.patient_id == patient.id) if patient else q.where(False)
    rows = (await db.scalars(q)).all()
    return ok([await _read_bill(db, b) for b in rows])

@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def create_payment(body: PaymentCreate, _: User = Depends(require_role([UserRole.ADMIN, UserRole.PHARMACY])), db: AsyncSession = Depends(get_db)):
    bill = await db.get(Bill, body.bill_id)
    if not bill: err("BILL_NOT_FOUND", "Bill not found.", 404)
    paid = await db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.bill_id == bill.id, Payment.payment_status == "PAID"))
    new_paid = Decimal(str(paid or 0)) + Decimal(str(body.amount))
    if new_paid > Decimal(str(bill.total_amount)): err("PAYMENT_EXCEEDS_BILL", "Payment exceeds the outstanding bill amount.", 422)
    payment = Payment(bill_id=bill.id, amount=body.amount, payment_method=body.payment_method, transaction_reference=body.transaction_reference, payment_status="PAID", paid_at=datetime.now(timezone.utc))
    db.add(payment); bill.payment_status = "PAID" if new_paid == Decimal(str(bill.total_amount)) else "PARTIAL"
    await db.commit(); await db.refresh(payment)
    return ok(PaymentRead.model_validate(payment).model_dump(mode="json"))

@router.get("/payments/{payment_id}")
async def get_payment(payment_id: UUID, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    payment = await db.get(Payment, payment_id)
    if not payment: err("PAYMENT_NOT_FOUND", "Payment not found.", 404)
    if current.role == UserRole.PATIENT:
        bill = await db.get(Bill, payment.bill_id); patient = await db.scalar(select(Patient).where(Patient.user_id == current.id))
        if not patient or bill.patient_id != patient.id: err("FORBIDDEN", "You do not have access to this payment.", 403)
    return ok(PaymentRead.model_validate(payment).model_dump(mode="json"))

@router.get("/{bill_id}")
async def get_bill(bill_id: UUID, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bill = await db.get(Bill, bill_id)
    if not bill: err("BILL_NOT_FOUND", "Bill not found.", 404)
    if current.role == UserRole.PATIENT:
        patient = await db.scalar(select(Patient).where(Patient.user_id == current.id))
        if not patient or bill.patient_id != patient.id: err("FORBIDDEN", "You do not have access to this bill.", 403)
    return ok(await _read_bill(db, bill))

@router.patch("/{bill_id}/status")
async def update_bill_status(bill_id: UUID, body: BillStatusUpdate, _: User = Depends(require_role([UserRole.ADMIN, UserRole.NURSE])), db: AsyncSession = Depends(get_db)):
    bill = await db.get(Bill, bill_id)
    if not bill: err("BILL_NOT_FOUND", "Bill not found.", 404)
    bill.payment_status = body.payment_status; await db.commit(); await db.refresh(bill)
    return ok(await _read_bill(db, bill))
