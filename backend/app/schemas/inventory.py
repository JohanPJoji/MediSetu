from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class InventoryBatchCreate(BaseModel):
    medicine_id: UUID
    batch_number: str = Field(min_length=1, max_length=100)
    expiry_date: date
    quantity: int = Field(ge=0)
    reorder_level: int = Field(default=10, ge=0)
    location: str | None = None
    status: str = "AVAILABLE"

class InventoryBatchUpdate(BaseModel):
    quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    location: str | None = None
    status: str | None = None

class InventoryBatchRead(InventoryBatchCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryTransactionCreate(BaseModel):
    medicine_id: UUID
    transaction_type: str = Field(min_length=1, max_length=32)
    quantity: int
    reference_id: str | None = None

class InventoryTransactionRead(BaseModel):
    id: UUID
    medicine_id: UUID
    transaction_type: str
    quantity: int
    reference_id: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
