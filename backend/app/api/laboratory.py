from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.laboratory import LabTest, LabOrder, LabResult
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.laboratory import LabTestCreate, LabTestRead, LabOrderCreate, LabOrderRead, LabOrderStatusUpdate, LabResultCreate, LabResultRead

router=APIRouter()

def ok(data): return {"success": True, "data": data, "message": None}
def err(code, message, status_code): raise HTTPException(status_code=status_code, detail={"code": code, "message": message})

@router.get("/tests")
async def list_tests(_: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows=(await db.scalars(select(LabTest).order_by(LabTest.name))).all()
    return ok([LabTestRead.model_validate(x).model_dump(mode="json") for x in rows])

@router.post("/tests", status_code=status.HTTP_201_CREATED)
async def create_test(body: LabTestCreate, _: User = Depends(require_role([UserRole.ADMIN, UserRole.NURSE])), db: AsyncSession = Depends(get_db)):
    if await db.scalar(select(LabTest).where(LabTest.code == body.code)):
        err("LAB_TEST_EXISTS", "A lab test with this code already exists.", 409)
    obj=LabTest(**body.model_dump()); db.add(obj); await db.commit(); await db.refresh(obj)
    return ok(LabTestRead.model_validate(obj).model_dump(mode="json"))

@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(body: LabOrderCreate, current: User = Depends(require_role([UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN])), db: AsyncSession = Depends(get_db)):
    patient=await db.get(Patient, body.patient_id); test=await db.get(LabTest, body.test_id); doctor=await db.get(User, body.doctor_id)
    if not patient or not test: err("REFERENCE_NOT_FOUND", "Patient or lab test not found.",404)
    if not doctor or doctor.role != UserRole.DOCTOR: err("DOCTOR_NOT_FOUND", "Selected doctor is not active.",404)
    obj=LabOrder(**body.model_dump()); db.add(obj); await db.commit(); await db.refresh(obj)
    return ok(LabOrderRead.model_validate(obj).model_dump(mode="json"))

@router.get("/orders")
async def list_orders(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q=select(LabOrder).order_by(LabOrder.ordered_at.desc())
    if current.role == UserRole.PATIENT:
        patient=await db.scalar(select(Patient).where(Patient.user_id == current.id))
        q=q.where(LabOrder.patient_id == patient.id) if patient else q.where(False)
    elif current.role == UserRole.DOCTOR:
        q=q.where(LabOrder.doctor_id == current.id)
    rows=(await db.scalars(q)).all(); return ok([LabOrderRead.model_validate(x).model_dump(mode="json") for x in rows])

@router.patch("/orders/{order_id}/status")
async def update_order(order_id: UUID, body: LabOrderStatusUpdate, current: User = Depends(require_role([UserRole.NURSE, UserRole.ADMIN, UserRole.DOCTOR])), db: AsyncSession = Depends(get_db)):
    obj=await db.get(LabOrder, order_id)
    if not obj: err("LAB_ORDER_NOT_FOUND", "Lab order not found.",404)
    if current.role == UserRole.DOCTOR and obj.doctor_id != current.id: err("FORBIDDEN", "You are not assigned to this lab order.",403)
    obj.status=body.status; obj.completed_at=datetime.now(timezone.utc) if body.status=="COMPLETED" else None
    await db.commit(); await db.refresh(obj); return ok(LabOrderRead.model_validate(obj).model_dump(mode="json"))

@router.post("/results", status_code=status.HTTP_201_CREATED)
async def create_result(body: LabResultCreate, _: User = Depends(require_role([UserRole.NURSE, UserRole.ADMIN])), db: AsyncSession = Depends(get_db)):
    order=await db.get(LabOrder, body.lab_order_id)
    if not order or order.test_id != body.test_id: err("LAB_ORDER_INVALID", "Lab order and test do not match.",400)
    if await db.scalar(select(LabResult).where(LabResult.lab_order_id == body.lab_order_id)): err("LAB_RESULT_EXISTS", "A result already exists for this order.",409)
    obj=LabResult(**body.model_dump()); db.add(obj); order.status="COMPLETED"; order.completed_at=datetime.now(timezone.utc); await db.commit(); await db.refresh(obj)
    return ok(LabResultRead.model_validate(obj).model_dump(mode="json"))

@router.get("/results/{result_id}")
async def get_result(result_id: UUID, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    obj=await db.get(LabResult, result_id)
    if not obj: err("LAB_RESULT_NOT_FOUND", "Lab result not found.",404)
    if current.role==UserRole.PATIENT:
        order=await db.get(LabOrder,obj.lab_order_id); patient=await db.scalar(select(Patient).where(Patient.user_id==current.id))
        if not patient or order.patient_id != patient.id: err("FORBIDDEN", "You do not have access to this result.",403)
    return ok(LabResultRead.model_validate(obj).model_dump(mode="json"))

@router.patch("/results/{result_id}/verify")
async def verify_result(result_id: UUID, current: User = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN])), db: AsyncSession = Depends(get_db)):
    obj=await db.get(LabResult,result_id)
    if not obj: err("LAB_RESULT_NOT_FOUND", "Lab result not found.",404)
    obj.verified_by=current.id; obj.verified_at=datetime.now(timezone.utc); await db.commit(); await db.refresh(obj)
    return ok(LabResultRead.model_validate(obj).model_dump(mode="json"))
