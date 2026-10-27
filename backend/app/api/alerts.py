from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.medicine_alert import MedicineAlert, AlternativeMedicine
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.alerts import MedicineAlertCreate, MedicineAlertRead, AlternativeMedicineCreate, AlternativeMedicineRead

router=APIRouter()
def ok(data): return {"success":True,"data":data,"message":None}
def err(code,message,status_code): raise HTTPException(status_code=status_code, detail={"code":code,"message":message})

@router.get("/medicine-alerts")
async def list_alerts(current:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    q=select(MedicineAlert).order_by(MedicineAlert.created_at.desc())
    if current.role==UserRole.PATIENT:
        patient=await db.scalar(select(Patient).where(Patient.user_id==current.id)); q=q.where(MedicineAlert.patient_id==patient.id) if patient else q.where(False)
    elif current.role==UserRole.DOCTOR: q=q.where(MedicineAlert.doctor_id==current.id)
    rows=(await db.scalars(q)).all(); return ok([MedicineAlertRead.model_validate(x).model_dump(mode="json") for x in rows])

@router.post("/medicine-alerts",status_code=status.HTTP_201_CREATED)
async def create_alert(body:MedicineAlertCreate,_:User=Depends(require_role([UserRole.DOCTOR,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    obj=MedicineAlert(**body.model_dump()); db.add(obj); await db.commit(); await db.refresh(obj); return ok(MedicineAlertRead.model_validate(obj).model_dump(mode="json"))

@router.patch("/medicine-alerts/{alert_id}/resolve")
async def resolve_alert(alert_id:UUID,current:User=Depends(require_role([UserRole.DOCTOR,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    obj=await db.get(MedicineAlert,alert_id)
    if not obj: err("ALERT_NOT_FOUND","Medicine alert not found.",404)
    if current.role==UserRole.DOCTOR and obj.doctor_id!=current.id: err("FORBIDDEN","You do not own this alert.",403)
    obj.status="RESOLVED"; await db.commit(); await db.refresh(obj); return ok(MedicineAlertRead.model_validate(obj).model_dump(mode="json"))

@router.post("/alternatives",status_code=status.HTTP_201_CREATED)
async def create_alternative(body:AlternativeMedicineCreate,current:User=Depends(require_role([UserRole.DOCTOR,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    obj=AlternativeMedicine(**body.model_dump(),created_by=current.id); db.add(obj); await db.commit(); await db.refresh(obj); return ok(AlternativeMedicineRead.model_validate(obj).model_dump(mode="json"))

@router.get("/medicines/{medicine_id}/alternatives")
async def list_alternatives(medicine_id:UUID,current:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    rows=(await db.scalars(select(AlternativeMedicine).where(AlternativeMedicine.medicine_id==medicine_id,AlternativeMedicine.status=="ACTIVE"))).all(); return ok([AlternativeMedicineRead.model_validate(x).model_dump(mode="json") for x in rows])
