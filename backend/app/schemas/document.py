from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class DocumentCreate(BaseModel):
    patient_id: UUID
    consultation_id: Optional[UUID] = None
    file_name: str
    file_type: str
    file_url: str
    extracted_text: Optional[str] = None

class DocumentRead(BaseModel):
    id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID]
    file_name: str
    file_type: str
    file_url: str
    extracted_text: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
