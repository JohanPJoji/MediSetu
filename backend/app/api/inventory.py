from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.inventory_batch import InventoryBatch
from app.models.medicine import Medicine
from app.models.inventory_transaction import InventoryTransaction
from app.models.user import User, UserRole
from app.schemas.inventory import InventoryBatchCreate, InventoryBatchUpdate, InventoryBatchRead, InventoryTransactionCreate, InventoryTransactionRead

router=APIRouter()
def ok(data): return {"success":True,"data":data,"message":None}
def err(code,message,status_code): raise HTTPException(status_code=status_code,detail={"code":code,"message":message})

@router.get("/batches")
async def list_batches(_:User=Depends(require_role([UserRole.PHARMACY,UserRole.ADMIN,UserRole.DOCTOR])),db:AsyncSession=Depends(get_db)):
    rows=(await db.scalars(select(InventoryBatch).order_by(InventoryBatch.expiry_date))).all(); return ok([InventoryBatchRead.model_validate(x).model_dump(mode="json") for x in rows])

@router.post("/batches",status_code=status.HTTP_201_CREATED)
async def create_batch(body:InventoryBatchCreate,_:User=Depends(require_role([UserRole.PHARMACY,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    obj=InventoryBatch(**body.model_dump()); db.add(obj); medicine=await db.get(Medicine, body.medicine_id)
    if not medicine: err("MEDICINE_NOT_FOUND","Medicine not found.",404)
    medicine.current_stock += body.quantity
    await db.commit(); await db.refresh(obj); return ok(InventoryBatchRead.model_validate(obj).model_dump(mode="json"))

@router.patch("/batches/{batch_id}")
async def update_batch(batch_id:UUID,body:InventoryBatchUpdate,_:User=Depends(require_role([UserRole.PHARMACY,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    obj=await db.get(InventoryBatch,batch_id);
    if not obj: err("BATCH_NOT_FOUND","Inventory batch not found.",404)
    updates=body.model_dump(exclude_unset=True)
    if "quantity" in updates:
        medicine=await db.get(Medicine,obj.medicine_id)
        if not medicine: err("MEDICINE_NOT_FOUND","Medicine not found.",404)
        medicine.current_stock += updates["quantity"] - obj.quantity
    for k,v in updates.items(): setattr(obj,k,v)
    await db.commit(); await db.refresh(obj); return ok(InventoryBatchRead.model_validate(obj).model_dump(mode="json"))

@router.get("/transactions")
async def list_transactions(_:User=Depends(require_role([UserRole.PHARMACY,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    rows=(await db.scalars(select(InventoryTransaction).order_by(InventoryTransaction.created_at.desc()))).all(); return ok([InventoryTransactionRead.model_validate(x).model_dump(mode="json") for x in rows])

@router.post("/transactions",status_code=status.HTTP_201_CREATED)
async def create_transaction(body:InventoryTransactionCreate,_:User=Depends(require_role([UserRole.PHARMACY,UserRole.ADMIN])),db:AsyncSession=Depends(get_db)):
    medicine=await db.get(Medicine,body.medicine_id)
    if not medicine: err("MEDICINE_NOT_FOUND","Medicine not found.",404)
    new_stock=medicine.current_stock + body.quantity
    if new_stock < 0: err("INSUFFICIENT_STOCK","Transaction would make stock negative.",400)
    medicine.current_stock=new_stock
    obj=InventoryTransaction(medicine_id=body.medicine_id,transaction_type=body.transaction_type,quantity=body.quantity,reference_id=body.reference_id); db.add(obj); await db.commit(); await db.refresh(obj); return ok(InventoryTransactionRead.model_validate(obj).model_dump(mode="json"))
