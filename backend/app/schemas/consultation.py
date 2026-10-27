from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.consultation import ConsultationStatus

class ConsultationBase(BaseModel):
    doctor_id: Optional[UUID] = None

class ConsultationCreate(ConsultationBase):
    patient_id: UUID

class ConsultationUpdate(BaseModel):
    doctor_id: Optional[UUID] = None
    status: Optional[ConsultationStatus] = None

class ConsultationRead(ConsultationBase):
    id: UUID
    patient_id: UUID
    status: ConsultationStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
