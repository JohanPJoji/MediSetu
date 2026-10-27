from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.referral import ReferralStatus

class ReferralCreate(BaseModel):
    consultation_id: UUID
    patient_id: UUID
    referred_doctor_id: Optional[UUID] = None
    reason: str
    notes: Optional[str] = None

class ReferralUpdate(BaseModel):
    status: ReferralStatus
    notes: Optional[str] = None

class ReferralRead(BaseModel):
    id: UUID
    consultation_id: UUID
    patient_id: UUID
    referring_doctor_id: Optional[UUID]
    referred_doctor_id: Optional[UUID]
    status: ReferralStatus
    reason: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
