from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class LabTestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    department: str | None = None
    price: float = Field(ge=0)
    sample_type: str | None = None

class LabTestRead(LabTestCreate):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LabOrderCreate(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    consultation_id: UUID | None = None
    test_id: UUID

class LabOrderRead(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    consultation_id: UUID | None
    test_id: UUID
    status: str
    ordered_at: datetime
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

class LabOrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ORDERED|SAMPLE_COLLECTED|PROCESSING|COMPLETED|CANCELLED)$")

class LabResultCreate(BaseModel):
    lab_order_id: UUID
    test_id: UUID
    result_value: str = Field(min_length=1)
    reference_range: str | None = None
    remarks: str | None = None

class LabResultRead(BaseModel):
    id: UUID
    lab_order_id: UUID
    test_id: UUID
    result_value: str
    reference_range: str | None
    remarks: str | None
    verified_by: UUID | None
    verified_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
