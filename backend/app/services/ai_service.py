"""AI-assisted clinical intake helpers.

The original MediSetu behavior is preserved as the default, deterministic path.
An optional OpenAI-compatible provider (including Omni Router) can be enabled via
configuration without making it a hard dependency for local development/tests.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import get_settings
from app.schemas.clinical_history import ClinicalHistoryCreate

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Deterministic HPI-component extraction helpers.
#
# These back-stop the external-LLM structured extraction path: whenever no
# external provider is configured (the default, deterministic MediSetu
# behavior used by the automated test suite), `generate_structured_history`
# must still populate `severity`/`duration`/`character` directly from the
# transcript text. Without this, those fields never leave `None` no matter
# what the patient says, which breaks two things: (1) explicit severity
# statements ("mild pain", "moderate pain", "severe pain") are silently
# dropped from the resulting clinical information, and (2)
# `detect_missing_information` (and therefore `ask_followup`) keeps asking
# the same question forever, because the very field it is checking for is
# never filled in even after the patient answers it.
# ──────────────────────────────────────────────────────────────────────────────

_SEVERITY_TERMS = ("mild", "moderate", "severe")

_CHARACTER_TERMS = (
    "sharp", "dull", "burning", "stabbing", "throbbing", "cramping",
    "crushing", "aching", "tight", "pressure", "squeezing", "shooting",
)

_DURATION_PATTERNS = [
    re.compile(r"\b(\d+)\s*(hour|hours|day|days|week|weeks|month|months|year|years)\b", re.IGNORECASE),
    re.compile(r"\bfor (a|the past) (few|couple of)?\s*(hour|hours|day|days|week|weeks|month|months)\b", re.IGNORECASE),
    re.compile(r"\bsince (yesterday|this morning|last night|last week|this week)\b", re.IGNORECASE),
]


def _extract_severity(text: str) -> str | None:
    lower = text.lower()
    for term in _SEVERITY_TERMS:
        if re.search(rf"\b{term}\b", lower):
            return term
    return None


def _extract_character(text: str) -> str | None:
    lower = text.lower()
    for term in _CHARACTER_TERMS:
        if re.search(rf"\b{term}\b", lower):
            return term
    return None


def _extract_duration(text: str) -> str | None:
    for pattern in _DURATION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return None


class LLMService:
    """Provider-agnostic clinical extraction, follow-up and summarization.

    The deterministic fallback never invents clinical facts.  When an
    OpenAI-compatible provider is explicitly configured, structured JSON output
    is requested for richer conversational follow-ups and doctor summaries.
    """

    def _external_enabled(self) -> bool:
        settings = get_settings()
        return bool(settings.LLM_API_KEY and settings.LLM_PROVIDER and settings.LLM_PROVIDER.lower() in {"openai", "omnirouter"})

    def _client_and_model(self):
        settings = get_settings()
        if not self._external_enabled():
            return None, None
        try:
            from openai import OpenAI

            base_url = settings.LLM_BASE_URL or (
                "https://api.omnirouter.ru/v1"
                if settings.LLM_PROVIDER and settings.LLM_PROVIDER.lower() == "omnirouter"
                else None
            )
            client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=base_url,
                timeout=float(settings.LLM_TIMEOUT_SECONDS),
            )
            model = settings.LLM_MODEL or "gpt-4o-mini"
            return client, model
        except Exception as exc:
            logger.warning("Optional external LLM could not be initialized: %s", exc)
            return None, None

    async def generate_structured_history(self, transcript_text: str) -> ClinicalHistoryCreate:
        text = transcript_text.strip()
        if not text:
            raise ValueError("Transcript is empty")

        client, model = self._client_and_model()
        if client is not None:
            try:
                prompt = (
                    "Extract only information explicitly present in this patient transcript. "
                    "Return JSON with fields chief_complaint, history_present_illness, onset, duration, "
                    "location, character, severity, timing, aggravating_factors, relieving_factors, "
                    "associated_symptoms, past_medical_history, past_surgical_history, medication_history, "
                    "allergies, red_flags. Do not invent values. red_flags must be a JSON array or null.\n\n"
                    f"Transcript:\n{text}"
                )
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a clinical documentation extractor. Never invent facts."},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0,
                )
                raw = response.choices[0].message.content or "{}"
                data = json.loads(raw)
                return ClinicalHistoryCreate.model_validate(data)
            except Exception as exc:
                logger.warning("External structured extraction failed; using deterministic fallback: %s", exc)

        # Preserve the original MediSetu deterministic implementation.
        lower = text.lower()
        chief_complaint = None
        for phrase in ("chest pain", "fever", "cough", "headache", "abdominal pain", "vomiting"):
            if phrase in lower:
                chief_complaint = phrase
                break

        red_flags = []
        if "severe chest pain" in lower:
            red_flags.append("Severe chest pain")
        if "difficulty breathing" in lower or "shortness of breath" in lower:
            red_flags.append("Breathing difficulty")

        return ClinicalHistoryCreate(
            chief_complaint=chief_complaint.capitalize() if chief_complaint else None,
            history_present_illness=text,
            severity=_extract_severity(text),
            duration=_extract_duration(text),
            character=_extract_character(text),
            red_flags=red_flags or None,
        )

    async def detect_missing_information(self, history: ClinicalHistoryCreate) -> list[str]:
        missing = []
        if not history.chief_complaint:
            missing.append("What is your main health concern?")
        if not history.duration:
            missing.append("How long have you had this problem?")
        if history.chief_complaint and history.chief_complaint.lower() in {"chest pain", "headache", "abdominal pain"} and not history.severity:
            missing.append("How severe is the pain?")
        if history.chief_complaint and history.chief_complaint.lower() in {"chest pain", "abdominal pain"} and not history.character:
            missing.append("How would you describe the pain?")
        return missing

    async def ask_followup(self, conversation_history: list[dict[str, str]]) -> tuple[str | None, bool]:
        """Return one focused follow-up question and completion state."""
        client, model = self._client_and_model()
        if client is not None:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a hospital intake assistant. Ask exactly ONE focused follow-up question at a time. "
                            "Do not diagnose, recommend medicines, or speculate. Return JSON: "
                            "{question: string, intake_complete: boolean}."
                        ),
                    }
                ]
                for turn in conversation_history:
                    role = "user" if turn.get("role") == "patient" else "assistant"
                    messages.append({"role": role, "content": turn.get("content", "")})
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                data = json.loads(response.choices[0].message.content or "{}")
                question = str(data.get("question") or "").strip() or None
                return question, bool(data.get("intake_complete"))
            except Exception as exc:
                logger.warning("External follow-up generation failed; using deterministic fallback: %s", exc)

        text = " ".join(turn.get("content", "") for turn in conversation_history if turn.get("role") == "patient")
        history = await self.generate_structured_history(text)
        questions = await self.detect_missing_information(history)
        return (questions[0] if questions else None), not bool(questions)

    async def summarize_transcript(self, transcript_text: str, history: ClinicalHistoryCreate | None = None) -> dict[str, Any]:
        """Create a doctor-facing case summary without changing stored schema."""
        text = transcript_text.strip()
        if not text:
            raise ValueError("Transcript is empty")
        structured = history or await self.generate_structured_history(text)

        client, model = self._client_and_model()
        if client is not None:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a clinical documentation assistant. Produce a concise doctor-facing summary "
                                "using ONLY facts in the transcript. Do not invent facts or diagnosis. Return JSON with "
                                "summary (string) and key_points (array of strings)."
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0,
                )
                data = json.loads(response.choices[0].message.content or "{}")
                summary = str(data.get("summary") or "").strip()
                key_points = [str(x) for x in data.get("key_points", [])]
                if summary:
                    return {"summary": summary, "key_points": key_points, "clinical_history": structured.model_dump()}
            except Exception as exc:
                logger.warning("External summarization failed; using deterministic summary: %s", exc)

        key_points: list[str] = []
        for label, value in (
            ("Chief complaint", structured.chief_complaint),
            ("Duration", structured.duration),
            ("Severity", structured.severity),
            ("Associated symptoms", structured.associated_symptoms),
            ("Past medical history", structured.past_medical_history),
            ("Medications", structured.medication_history),
            ("Allergies", structured.allergies),
        ):
            if value:
                key_points.append(f"{label}: {value}")

        summary = structured.history_present_illness or structured.chief_complaint or "No clinical summary available."
        return {"summary": summary, "key_points": key_points, "clinical_history": structured.model_dump()}

    async def suggest_medicines(self, case_summary: dict[str, Any]) -> list[dict[str, Any]]:
        """Optional doctor-only medicine suggestions. Never persisted automatically."""
        client, model = self._client_and_model()
        if client is None:
            return []
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a clinical pharmacology assistant. Provide medication considerations ONLY for doctor review. "
                            "Do not present them as prescriptions. Return a JSON object with suggestions: array of {name,dosage,frequency,duration,notes}."
                        ),
                    },
                    {"role": "user", "content": json.dumps(case_summary)},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            return list(data.get("suggestions", []))
        except Exception as exc:
            logger.warning("External medicine suggestion failed: %s", exc)
            return []


class STTService:
    """Local speech-to-text with optional deterministic mock fallback."""

    async def transcribe(self, audio: bytes, language: str = "en-IN", content_type: str = "audio/webm") -> dict[str, Any]:
        settings = get_settings()
        if settings.STT_PROVIDER == "mock":
            if settings.MOCK_TRANSCRIPT:
                return {"transcript": settings.MOCK_TRANSCRIPT, "confidence": 1.0, "is_low_confidence": False, "retry_message": None}
            raise RuntimeError("Mock STT is enabled but MOCK_TRANSCRIPT is not configured")

        from fastapi.concurrency import run_in_threadpool
        from app.services.voice_service import transcribe_audio

        result = await run_in_threadpool(
            transcribe_audio, audio, content_type, language_code=language
        )
        return {
            "transcript": result.transcript,
            "confidence": result.confidence,
            "is_low_confidence": result.is_low_confidence,
            "retry_message": result.retry_message,
        }


class TTSService:
    """Optional local Windows TTS. Returns empty bytes when unavailable."""

    async def synthesize(self, text: str, language: str = "en-IN") -> bytes:
        from app.services.voice_service import synthesize_speech

        return synthesize_speech(text, language_code=language)


stt_service = STTService()
llm_service = LLMService()
tts_service = TTSService()
