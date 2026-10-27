import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base

class ClinicalHistory(Base):
    __tablename__ = "clinical_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    chief_complaint = Column(Text, nullable=True)
    history_present_illness = Column(Text, nullable=True)
    
    # HPI components
    onset = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    location = Column(String, nullable=True)
    character = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    timing = Column(String, nullable=True)
    aggravating_factors = Column(String, nullable=True)
    relieving_factors = Column(String, nullable=True)
    associated_symptoms = Column(String, nullable=True)
    
    # Past history
    past_medical_history = Column(Text, nullable=True)
    past_surgical_history = Column(Text, nullable=True)
    medication_history = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    
    # AI detection
    red_flags = Column(JSONB, nullable=True) # list of detected red flags
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    consultation = relationship("Consultation", backref="clinical_history")
