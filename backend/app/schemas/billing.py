from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class BillItemCreate(BaseModel):
    item_type: str = Field(min_length=1, max_length=32)
    item_reference_id: str | None = None
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(ge=0)

class BillItemRead(BillItemCreate):
    id: UUID
    total_price: float
    model_config = ConfigDict(from_attributes=True)

class BillCreate(BaseModel):
    patient_id: UUID
    consultation_id: UUID | None = None
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    items: list[BillItemCreate] = Field(min_length=1)

class BillRead(BaseModel):
    id: UUID
    bill_number: str
    patient_id: UUID
    consultation_id: UUID | None
    subtotal: float
    discount: float
    tax: float
    total_amount: float
    payment_status: str
    created_at: datetime
    items: list[BillItemRead]
    model_config = ConfigDict(from_attributes=True)

class BillStatusUpdate(BaseModel):
    payment_status: str = Field(pattern="^(PENDING|PARTIAL|PAID|CANCELLED)$")

class PaymentCreate(BaseModel):
    bill_id: UUID
    amount: float = Field(gt=0)
    payment_method: str = Field(min_length=2, max_length=32)
    transaction_reference: str | None = None

class PaymentRead(BaseModel):
    id: UUID
    bill_id: UUID
    amount: float
    payment_method: str
    transaction_reference: str | None
    payment_status: str
    paid_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
