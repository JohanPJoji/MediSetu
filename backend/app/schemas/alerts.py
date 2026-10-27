from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class MedicineAlertCreate(BaseModel):
    prescription_id: UUID
    medicine_id: UUID
    patient_id: UUID
    doctor_id: UUID
    required_quantity: int = Field(gt=0)
    available_quantity: int = Field(ge=0)
    reason: str | None = None

class MedicineAlertRead(MedicineAlertCreate):
    id: UUID
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AlternativeMedicineCreate(BaseModel):
    medicine_id: UUID
    alternative_medicine_id: UUID
    status: str = "ACTIVE"

class AlternativeMedicineRead(AlternativeMedicineCreate):
    id: UUID
    created_by: UUID | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
