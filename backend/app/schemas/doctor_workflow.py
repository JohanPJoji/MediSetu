from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.prescription import PrescriptionStatus

# Diagnosis Schemas
class DiagnosisCreate(BaseModel):
    condition: str = Field(min_length=1, max_length=500)
    notes: Optional[str] = None

class DiagnosisRead(BaseModel):
    id: UUID
    consultation_id: UUID
    doctor_id: Optional[UUID]
    condition: str
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Prescription Schemas
class PrescriptionItemCreate(BaseModel):
    medicine_id: UUID
    dosage: str
    frequency: str
    duration: str
    quantity: int = Field(gt=0)

class PrescriptionItemRead(BaseModel):
    id: UUID
    medicine_id: UUID
    dosage: str
    frequency: str
    duration: str
    quantity: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)

class PrescriptionCreate(BaseModel):
    consultation_id: UUID
    patient_id: UUID
    notes: Optional[str] = None
    items: List[PrescriptionItemCreate] = Field(min_length=1)

class PrescriptionRead(BaseModel):
    id: UUID
    consultation_id: UUID
    doctor_id: Optional[UUID]
    patient_id: UUID
    status: PrescriptionStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[PrescriptionItemRead]

    model_config = ConfigDict(from_attributes=True)

class PrescriptionUpdate(BaseModel):
    status: PrescriptionStatus
