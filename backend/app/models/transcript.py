import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base

class TranscriptRole(str, enum.Enum):
    PATIENT = "PATIENT"
    SYSTEM = "SYSTEM"

class TranscriptEntry(Base):
    __tablename__ = "transcript_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(Enum(TranscriptRole, name="transcript_role"), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String, nullable=False, default="en")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    consultation = relationship("Consultation", backref="transcript_entries")
