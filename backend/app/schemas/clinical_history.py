from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ClinicalHistoryCreate(BaseModel):
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    onset: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    character: Optional[str] = None
    severity: Optional[str] = None
    timing: Optional[str] = None
    aggravating_factors: Optional[str] = None
    relieving_factors: Optional[str] = None
    associated_symptoms: Optional[str] = None
    past_medical_history: Optional[str] = None
    past_surgical_history: Optional[str] = None
    medication_history: Optional[str] = None
    allergies: Optional[str] = None
    family_history: Optional[str] = None
    red_flags: Optional[List[str]] = None

class ClinicalHistoryUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    onset: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    character: Optional[str] = None
    severity: Optional[str] = None
    timing: Optional[str] = None
    aggravating_factors: Optional[str] = None
    relieving_factors: Optional[str] = None
    associated_symptoms: Optional[str] = None
    past_medical_history: Optional[str] = None
    past_surgical_history: Optional[str] = None
    medication_history: Optional[str] = None
    allergies: Optional[str] = None
    family_history: Optional[str] = None
    red_flags: Optional[List[str]] = None

class ClinicalHistoryRead(BaseModel):
    id: UUID
    consultation_id: UUID
    chief_complaint: Optional[str]
    history_present_illness: Optional[str]
    onset: Optional[str]
    duration: Optional[str]
    location: Optional[str]
    character: Optional[str]
    severity: Optional[str]
    timing: Optional[str]
    aggravating_factors: Optional[str]
    relieving_factors: Optional[str]
    associated_symptoms: Optional[str]
    past_medical_history: Optional[str]
    past_surgical_history: Optional[str]
    medication_history: Optional[str]
    allergies: Optional[str]
    family_history: Optional[str]
    red_flags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
