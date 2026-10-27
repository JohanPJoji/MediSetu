from uuid import UUID
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.consultation import ConsultationStatus
from app.schemas.consultation import ConsultationCreate, ConsultationRead, ConsultationUpdate
from app.schemas.transcript import TranscriptEntryCreate, TranscriptEntryRead
from app.schemas.clinical_history import ClinicalHistoryCreate, ClinicalHistoryUpdate, ClinicalHistoryRead
from app.schemas.doctor_workflow import DiagnosisCreate, DiagnosisRead
from app.services import (
    consultation_service,
    patient_service,
    transcript_service,
    clinical_history_service,
    doctor_workflow_service,
)
from app.services.ai_service import llm_service, stt_service
from app.services.safety_service import check_for_emergency
from app.schemas.voice import VoiceInputResponse, FollowUpResponse, SummaryResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _success_response(data):
    return {"success": True, "data": data, "message": None}


async def _get_patient_for_user(db: AsyncSession, user: User):
    return await patient_service.get_patient_by_user_id(db, user.id)


async def _authorize_consultation(
    db: AsyncSession, consultation, current_user: User, *, allow_patient: bool = True
) -> None:
    """Enforce resource-level authorization for a consultation."""
    if consultation is None:
        _error_response(status.HTTP_404_NOT_FOUND, "CONSULTATION_NOT_FOUND", "Consultation not found")

    if current_user.role == UserRole.PATIENT:
        if not allow_patient:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Forbidden")
        patient = await _get_patient_for_user(db, current_user)
        if not patient or consultation.patient_id != patient.id:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "You are not authorized for this consultation")
        return

    if current_user.role == UserRole.DOCTOR:
        if consultation.doctor_id != current_user.id:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Doctor is not assigned to this consultation")
        return

    if current_user.role in (UserRole.NURSE, UserRole.ADMIN):
        return

    _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Forbidden")


def _serialize(consultation) -> dict:
    return ConsultationRead.model_validate(consultation).model_dump(mode="json")


async def _flag_emergency_if_needed(db: AsyncSession, consultation_id: UUID, entry) -> dict:
    """Run the same deterministic safety pipeline used by /voice-input against a
    freshly created PATIENT transcript entry, regardless of whether it arrived by
    voice, typing, or a follow-up answer (see safety_service.check_for_emergency).

    Returns a dict of extra `is_emergency` / `emergency_instructions` fields to
    merge into the entry's response payload. When an emergency is detected, a
    SYSTEM transcript entry with the fixed emergency message is appended to the
    same conversation, mirroring what /voice-input already does, so the warning
    is visible to anyone (patient or doctor) reading the transcript afterwards.
    """
    from app.models.transcript import TranscriptRole

    if entry.role != TranscriptRole.PATIENT:
        return {"is_emergency": False, "emergency_instructions": None}

    red_flag = check_for_emergency(entry.content)
    if not red_flag.is_emergency:
        return {"is_emergency": False, "emergency_instructions": None}

    await transcript_service.create_transcript_entry(
        db,
        consultation_id,
        TranscriptEntryCreate(role=TranscriptRole.SYSTEM, content=red_flag.emergency_message, language="en"),
    )
    return {"is_emergency": True, "emergency_instructions": red_flag.emergency_message}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation_in: ConsultationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.PATIENT:
        patient = await _get_patient_for_user(db, current_user)
        if not patient or patient.id != consultation_in.patient_id:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "A patient can only create consultations for themselves")
        doctor_id = None
    elif current_user.role == UserRole.DOCTOR:
        patient = await patient_service.get_patient_by_id(db, consultation_in.patient_id)
        if not patient:
            _error_response(status.HTTP_404_NOT_FOUND, "PATIENT_NOT_FOUND", "Patient not found")
        doctor_id = consultation_in.doctor_id or current_user.id
        if doctor_id != current_user.id:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Doctors can only create consultations assigned to themselves")
    elif current_user.role in (UserRole.NURSE, UserRole.ADMIN):
        patient = await patient_service.get_patient_by_id(db, consultation_in.patient_id)
        if not patient:
            _error_response(status.HTTP_404_NOT_FOUND, "PATIENT_NOT_FOUND", "Patient not found")
        doctor_id = consultation_in.doctor_id
    else:
        _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Forbidden")

    payload = ConsultationCreate(patient_id=consultation_in.patient_id, doctor_id=doctor_id)
    consultation = await consultation_service.create_consultation(db, payload)
    return _success_response(_serialize(consultation))


@router.get("")
async def list_consultations(
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.PATIENT:
        patient = await _get_patient_for_user(db, current_user)
        consultations = await consultation_service.list_consultations(db, patient_id=patient.id) if patient else []
    elif current_user.role == UserRole.DOCTOR:
        consultations = await consultation_service.list_consultations(db, doctor_id=current_user.id)
    else:
        consultations = await consultation_service.list_consultations(db)

    return _success_response([_serialize(c) for c in consultations])


@router.get("/{consultation_id}")
async def get_consultation(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    return _success_response(_serialize(consultation))


@router.patch("/{consultation_id}/status")
async def update_consultation_status(
    consultation_id: UUID,
    status_update: ConsultationUpdate,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if status_update.status is None:
        _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", "Status must be provided")

    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)

    if current_user.role == UserRole.PATIENT:
        await _authorize_consultation(db, consultation, current_user)
        if consultation.status == ConsultationStatus.CREATED and status_update.status != ConsultationStatus.IN_PROGRESS:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Patients can only start a created consultation")
        if consultation.status == ConsultationStatus.IN_PROGRESS and status_update.status != ConsultationStatus.CANCELLED:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Patients can only cancel an in-progress consultation")
    else:
        await _authorize_consultation(db, consultation, current_user)

    try:
        updated = await consultation_service.update_consultation_status(db, consultation_id, status_update.status)
    except consultation_service.ConsultationNotFoundError:
        _error_response(status.HTTP_404_NOT_FOUND, "CONSULTATION_NOT_FOUND", "Consultation not found")
    except consultation_service.InvalidStateTransitionError as exc:
        _error_response(status.HTTP_400_BAD_REQUEST, "INVALID_STATE_TRANSITION", str(exc))

    return _success_response(_serialize(updated))


@router.patch("/{consultation_id}/assign")
async def assign_doctor(
    consultation_id: UUID,
    assignment: ConsultationUpdate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if assignment.doctor_id is None:
        _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", "doctor_id must be provided")

    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    if consultation is None:
        _error_response(status.HTTP_404_NOT_FOUND, "CONSULTATION_NOT_FOUND", "Consultation not found")

    if current_user.role == UserRole.DOCTOR:
        if assignment.doctor_id != current_user.id:
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Doctors can only assign consultations to themselves")
        if consultation.doctor_id not in (None, current_user.id):
            _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Consultation is assigned to another doctor")

    try:
        updated = await consultation_service.assign_doctor(db, consultation_id, assignment.doctor_id)
    except consultation_service.InvalidDoctorAssignmentError as exc:
        _error_response(status.HTTP_400_BAD_REQUEST, "INVALID_DOCTOR", str(exc))
    return _success_response(_serialize(updated))


@router.post("/{consultation_id}/transcript", status_code=status.HTTP_201_CREATED)
async def add_transcript_entry(
    consultation_id: UUID,
    entry_in: TranscriptEntryCreate,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    if current_user.role == UserRole.PATIENT and entry_in.role.name != "PATIENT":
        _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Patients may only add patient transcript entries")
    entry = await transcript_service.create_transcript_entry(db, consultation_id, entry_in)

    # Every patient message must go through the same emergency/safety check,
    # regardless of whether it arrived by voice, typing, or a follow-up
    # answer. Previously only /voice-input ran this check, so a typed
    # emergency message (this endpoint) or a legacy /audio upload silently
    # skipped safety detection entirely.
    response_data = TranscriptEntryRead.model_validate(entry).model_dump(mode="json")
    response_data.update(await _flag_emergency_if_needed(db, consultation_id, entry))
    return _success_response(response_data)




@router.post("/{consultation_id}/audio")
async def ingest_patient_audio(
    consultation_id: UUID,
    audio: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe a patient audio sample and append it to the consultation transcript."""
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)

    content = await audio.read()
    if not content:
        _error_response(status.HTTP_400_BAD_REQUEST, "EMPTY_AUDIO", "The uploaded audio file is empty")
    try:
        stt_result = await stt_service.transcribe(content, language="en-IN", content_type=audio.content_type or "audio/wav")
        transcript = stt_result["transcript"]
        from app.models.transcript import TranscriptRole
        entry = await transcript_service.create_transcript_entry(
            db,
            consultation_id,
            TranscriptEntryCreate(role=TranscriptRole.PATIENT, content=transcript),
        )
    except Exception as exc:
        _error_response(status.HTTP_502_BAD_GATEWAY, "STT_ERROR", str(exc))

    response_data = TranscriptEntryRead.model_validate(entry).model_dump(mode="json")
    response_data.update(await _flag_emergency_if_needed(db, consultation_id, entry))
    return _success_response(response_data)


@router.post("/{consultation_id}/voice-input", response_model=None)
async def voice_input(
    consultation_id: UUID,
    audio: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Full conversational voice intake pipeline, adapted to MediSetu's consultation model.

    Audio is transcribed locally with faster-whisper, safety patterns are checked
    before AI follow-up generation, the transcript is persisted in the existing
    transcript table, and an optional local TTS reply is returned as a data URL.
    The existing `/audio` endpoint remains unchanged for backwards compatibility.
    """
    import asyncio
    from fastapi.concurrency import run_in_threadpool
    from app.models.transcript import TranscriptRole

    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)

    content = await audio.read()
    if not content:
        _error_response(status.HTTP_400_BAD_REQUEST, "EMPTY_AUDIO", "The uploaded audio file is empty")

    content_type = audio.content_type or "audio/webm"
    try:
        stt_result = await stt_service.transcribe(content, language="en-IN", content_type=content_type)
    except Exception as exc:
        logger.exception("Voice transcription failed for consultation %s", consultation_id)
        _error_response(status.HTTP_502_BAD_GATEWAY, "STT_ERROR", str(exc))

    transcript = str(stt_result.get("transcript") or "").strip()
    confidence = float(stt_result.get("confidence") or 0.0)
    low_confidence = bool(stt_result.get("is_low_confidence"))
    assistant_message = str(stt_result.get("retry_message") or "Please try again.") if low_confidence else ""
    is_emergency = False
    emergency_instructions = None
    intake_complete = False
    follow_up_questions: list[str] = []

    if not low_confidence and transcript:
        red_flag = check_for_emergency(transcript)
        if red_flag.is_emergency:
            is_emergency = True
            emergency_instructions = red_flag.emergency_message
            assistant_message = red_flag.voice_message or red_flag.emergency_message or "Please seek immediate medical attention."
            await transcript_service.create_transcript_entry(
                db,
                consultation_id,
                TranscriptEntryCreate(role=TranscriptRole.PATIENT, content=transcript, language="en-IN"),
            )
        else:
            await transcript_service.create_transcript_entry(
                db,
                consultation_id,
                TranscriptEntryCreate(role=TranscriptRole.PATIENT, content=transcript, language="en-IN"),
            )
            entries = await transcript_service.list_transcript_entries(db, consultation_id)
            history = [
                {"role": "patient" if entry.role == TranscriptRole.PATIENT else "assistant", "content": entry.content}
                for entry in entries
            ]
            try:
                question, llm_intake_complete = await llm_service.ask_followup(history)
                intake_complete = llm_intake_complete
                if question:
                    follow_up_questions = [question]
                    assistant_message = question
                elif intake_complete:
                    assistant_message = (
                        "Thank you. I have collected the available intake information. "
                        "You can process the consultation for clinical history when ready."
                    )
                else:
                    follow_up_questions = await llm_service.detect_missing_information(
                        await llm_service.generate_structured_history(" ".join(e["content"] for e in history if e["role"] == "patient"))
                    )
                    assistant_message = follow_up_questions[0] if follow_up_questions else "Thank you. Please continue when ready."
            except Exception as exc:
                logger.warning("Follow-up generation failed for consultation %s: %s", consultation_id, exc)
                assistant_message = "Your voice response was recorded. You can continue by typing the next response."

    if assistant_message:
        await transcript_service.create_transcript_entry(
            db,
            consultation_id,
            TranscriptEntryCreate(role=TranscriptRole.SYSTEM, content=assistant_message, language="en"),
        )

    audio_response_url = None
    if assistant_message:
        try:
            from app.services.voice_service import synthesize_speech
            audio_bytes = await asyncio.wait_for(
                run_in_threadpool(synthesize_speech, assistant_message, "en-IN"),
                timeout=30.0,
            )
            if audio_bytes:
                audio_response_url = f"data:audio/wav;base64,{base64.b64encode(audio_bytes).decode()}"
        except Exception as exc:
            # TTS is optional; never fail the clinical workflow if local TTS is unavailable.
            logger.info("Optional TTS unavailable for consultation %s: %s", consultation_id, exc)

    return _success_response(
        VoiceInputResponse(
            consultation_id=str(consultation_id),
            transcript=transcript,
            stt_confidence=confidence,
            assistant_message=assistant_message,
            follow_up_questions=follow_up_questions,
            audio_response_url=audio_response_url,
            low_confidence_retry=low_confidence,
            is_emergency=is_emergency,
            emergency_instructions=emergency_instructions,
            intake_complete=intake_complete,
        ).model_dump(mode="json")
    )


@router.post("/{consultation_id}/follow-up", response_model=None)
async def generate_follow_up(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Generate the next focused intake question from the existing transcript."""
    from app.models.transcript import TranscriptRole

    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    entries = await transcript_service.list_transcript_entries(db, consultation_id)
    if not entries:
        _error_response(status.HTTP_400_BAD_REQUEST, "NO_TRANSCRIPT", "No transcript entries to use for follow-up generation")

    patient_text = " ".join(e.content for e in entries if e.role == TranscriptRole.PATIENT)
    if check_for_emergency(patient_text).is_emergency:
        _error_response(status.HTTP_409_CONFLICT, "EMERGENCY_DETECTED", "Emergency red flags were detected; continue with urgent care rather than routine intake questions")

    history = [
        {"role": "patient" if e.role == TranscriptRole.PATIENT else "assistant", "content": e.content}
        for e in entries
    ]
    question, intake_complete = await llm_service.ask_followup(history)
    questions = [question] if question else []
    return _success_response(
        FollowUpResponse(
            consultation_id=str(consultation_id),
            question=question,
            follow_up_questions=questions,
            intake_complete=intake_complete,
        ).model_dump(mode="json")
    )


@router.get("/{consultation_id}/summary", response_model=None)
async def summarize_consultation(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Return a doctor/staff-facing transcript summary without changing stored consultation data."""
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    entries = await transcript_service.list_transcript_entries(db, consultation_id)
    if not entries:
        _error_response(status.HTTP_400_BAD_REQUEST, "NO_TRANSCRIPT", "No transcript entries to summarize")

    transcript_text = " ".join(e.content for e in entries)
    structured = await llm_service.generate_structured_history(transcript_text)
    summary = await llm_service.summarize_transcript(transcript_text, structured)
    follow_up_questions = await llm_service.detect_missing_information(structured)
    return _success_response(
        SummaryResponse(
            consultation_id=str(consultation_id),
            summary=summary["summary"],
            key_points=summary["key_points"],
            clinical_history=summary["clinical_history"],
            follow_up_questions=follow_up_questions,
        ).model_dump(mode="json")
    )


@router.get("/{consultation_id}/transcript")
async def get_transcript(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    entries = await transcript_service.list_transcript_entries(db, consultation_id)
    return _success_response([TranscriptEntryRead.model_validate(e).model_dump(mode="json") for e in entries])


@router.post("/{consultation_id}/clinical-history", status_code=status.HTTP_201_CREATED)
async def create_clinical_history(
    consultation_id: UUID,
    history_in: ClinicalHistoryCreate,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    try:
        history = await clinical_history_service.create_clinical_history(db, consultation_id, history_in)
    except clinical_history_service.ClinicalHistoryAlreadyExistsError:
        _error_response(status.HTTP_409_CONFLICT, "CLINICAL_HISTORY_EXISTS", "Clinical history already exists")
    return _success_response(ClinicalHistoryRead.model_validate(history).model_dump(mode="json"))


@router.get("/{consultation_id}/clinical-history")
async def get_clinical_history(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    history = await clinical_history_service.get_clinical_history_by_consultation_id(db, consultation_id)
    if history is None:
        _error_response(status.HTTP_404_NOT_FOUND, "HISTORY_NOT_FOUND", "Clinical history not found")
    return _success_response(ClinicalHistoryRead.model_validate(history).model_dump(mode="json"))


@router.patch("/{consultation_id}/clinical-history")
async def update_clinical_history(
    consultation_id: UUID,
    history_update: ClinicalHistoryUpdate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    try:
        history = await clinical_history_service.update_clinical_history(db, consultation_id, history_update)
    except clinical_history_service.ClinicalHistoryNotFoundError:
        _error_response(status.HTTP_404_NOT_FOUND, "HISTORY_NOT_FOUND", "Clinical history not found")
    return _success_response(ClinicalHistoryRead.model_validate(history).model_dump(mode="json"))


@router.post("/{consultation_id}/process-intake")
async def process_intake(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    entries = await transcript_service.list_transcript_entries(db, consultation_id)
    if not entries:
        _error_response(status.HTTP_400_BAD_REQUEST, "NO_TRANSCRIPT", "No transcript entries to process")

    transcript_text = " ".join(entry.content for entry in entries)
    try:
        structured_data = await llm_service.generate_structured_history(transcript_text)
        history = await clinical_history_service.get_clinical_history_by_consultation_id(db, consultation_id)
        if history:
            history = await clinical_history_service.update_clinical_history(
                db, consultation_id, ClinicalHistoryUpdate.model_validate(structured_data.model_dump())
            )
        else:
            history = await clinical_history_service.create_clinical_history(
                db, consultation_id, structured_data
            )
        follow_up_questions = await llm_service.detect_missing_information(structured_data)
    except Exception:
        logger.exception("AI processing failed for consultation %s", consultation_id)
        _error_response(
            status.HTTP_502_BAD_GATEWAY,
            "AI_PROCESSING_ERROR",
            "The clinical AI service could not process this consultation.",
        )

    response_data = {
        "clinical_history": ClinicalHistoryRead.model_validate(history).model_dump(mode="json"),
        "follow_up_questions": follow_up_questions,
        "triage_alert": bool(structured_data.red_flags),
    }
    return _success_response(response_data)


@router.post("/{consultation_id}/ai-suggestions", response_model=None)
async def generate_doctor_ai_suggestions(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Return optional doctor-only AI medicine considerations without persisting them."""
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    entries = await transcript_service.list_transcript_entries(db, consultation_id)
    if not entries:
        _error_response(status.HTTP_400_BAD_REQUEST, "NO_TRANSCRIPT", "No transcript available")
    transcript_text = " ".join(entry.content for entry in entries)
    structured = await llm_service.generate_structured_history(transcript_text)
    summary = await llm_service.summarize_transcript(transcript_text, structured)
    medicines = await llm_service.suggest_medicines(summary["clinical_history"])
    return _success_response({
        "consultation_id": str(consultation_id),
        "doctor_only": True,
        "suggestions": medicines,
        "note": "AI suggestions are decision support only. The doctor must independently review and prescribe.",
    })


@router.post("/{consultation_id}/diagnosis", status_code=status.HTTP_201_CREATED)
async def create_diagnosis(
    consultation_id: UUID,
    diagnosis_in: DiagnosisCreate,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    diagnosis = await doctor_workflow_service.create_diagnosis(db, consultation_id, current_user.id, diagnosis_in)
    return _success_response(DiagnosisRead.model_validate(diagnosis).model_dump(mode="json"))


@router.get("/{consultation_id}/diagnosis")
async def get_diagnoses(
    consultation_id: UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    consultation = await consultation_service.get_consultation_by_id(db, consultation_id)
    await _authorize_consultation(db, consultation, current_user)
    diagnoses = await doctor_workflow_service.get_diagnoses_by_consultation(db, consultation_id)
    return _success_response([DiagnosisRead.model_validate(d).model_dump(mode="json") for d in diagnoses])
