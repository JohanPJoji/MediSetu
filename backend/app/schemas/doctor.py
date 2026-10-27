from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DoctorCreate(BaseModel):
    user_id: UUID
    name: str = Field(min_length=1, max_length=255)
    department: str | None = None
    specialization: str | None = None
    registration_number: str | None = None
    is_available: bool = True


class DoctorRead(DoctorCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
