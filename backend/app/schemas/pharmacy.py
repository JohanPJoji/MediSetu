from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.pharmacy_order import PharmacyOrderStatus


class PharmacyOrderRead(BaseModel):
    id: UUID
    prescription_id: UUID
    patient_id: UUID
    status: PharmacyOrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PharmacyOrderStatusUpdate(BaseModel):
    status: PharmacyOrderStatus
