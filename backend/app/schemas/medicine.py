from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    current_stock: int = Field(default=0, ge=0)

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    current_stock: Optional[int] = Field(default=None, ge=0)

class MedicineRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    current_stock: int
    reserved_stock: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
