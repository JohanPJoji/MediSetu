from typing import Any
from pydantic import BaseModel, Field


class VoiceInputResponse(BaseModel):
    consultation_id: str
    transcript: str
    stt_confidence: float = 0.0
    assistant_message: str
    follow_up_questions: list[str] = Field(default_factory=list)
    audio_response_url: str | None = None
    low_confidence_retry: bool = False
    is_emergency: bool = False
    emergency_instructions: str | None = None
    intake_complete: bool = False


class FollowUpResponse(BaseModel):
    consultation_id: str
    question: str | None = None
    follow_up_questions: list[str] = Field(default_factory=list)
    intake_complete: bool = False


class SummaryResponse(BaseModel):
    consultation_id: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    clinical_history: dict[str, Any]
    follow_up_questions: list[str] = Field(default_factory=list)
