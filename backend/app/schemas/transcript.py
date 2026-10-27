from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.transcript import TranscriptRole

class TranscriptEntryCreate(BaseModel):
    role: TranscriptRole
    content: str
    language: str = "en"

class TranscriptEntryRead(BaseModel):
    id: UUID
    consultation_id: UUID
    role: TranscriptRole
    content: str
    language: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
