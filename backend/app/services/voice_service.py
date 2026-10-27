"""
voice_service.py — Local Speech-to-Text and optional Text-to-Speech.

STT uses faster-whisper locally. TTS uses pyttsx3 on Windows when available;
TTS is optional and never blocks transcription if unavailable.

Architecture:
  Audio → faster-whisper → existing MediSetu transcript store → intake follow-up → optional TTS

All public function names, signatures, dataclasses (TranscriptResult, AudioValidationError)
and return types are UNCHANGED — routers/patient.py requires zero edits.

Setup:
  Install backend requirements. faster-whisper downloads its configured model on first use.
  On Windows, pyttsx3 uses an installed SAPI5 voice for optional TTS.
"""

from __future__ import annotations

import io
import logging
import os
import platform
import tempfile
from dataclasses import dataclass

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Optional local TTS dependencies. These are only available/importable on a
# machine that has `pyttsx3` installed (see backend/requirements.txt) and,
# for the SAPI5 driver specifically, on Windows with `pywin32` installed.
# Previously these names were referenced directly in `synthesize_speech`
# without being imported anywhere in this module, which meant every TTS
# call raised a `NameError` instead of the intended "TTS unavailable"
# `RuntimeError` — silently defeating the optional-TTS feature on every
# platform, Windows included. Import them defensively here instead so the
# rest of the module can check for `None` and fail in the documented,
# caught-by-the-caller way.
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # type: ignore[assignment]

try:
    import pythoncom  # Windows-only (pywin32); used to init COM for SAPI5 in a threadpool.
except ImportError:
    pythoncom = None  # type: ignore[assignment]


# ──────────────────────────────────────────────────────────────────────────────
# faster-whisper model — lazy singleton, loaded once on first STT call
# ──────────────────────────────────────────────────────────────────────────────

_whisper_model = None  # type: ignore[assignment]


def _get_whisper_model():
    """Load the faster-whisper model on first use. Cached after that."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from exc

    model_size = settings.WHISPER_MODEL_SIZE          # e.g. "base", "small", "medium"
    model_dir  = settings.WHISPER_MODEL_DIR or None   # None = auto-download to ~/.cache

    device     = settings.WHISPER_DEVICE              # "cpu" or "cuda"
    compute    = settings.WHISPER_COMPUTE_TYPE        # "int8" (cpu) or "float16" (cuda)

    logger.info(
        "Loading faster-whisper model '%s' on device='%s' compute_type='%s'",
        model_size, device, compute,
    )

    _whisper_model = WhisperModel(
        model_size_or_path=model_dir if model_dir else model_size,
        device=device,
        compute_type=compute,
    )
    logger.info("faster-whisper model loaded.")
    return _whisper_model


# ──────────────────────────────────────────────────────────────────────────────
# Format + size validation  (public API unchanged)
# ──────────────────────────────────────────────────────────────────────────────

# MIME types accepted by the backend endpoint
_MIME_TO_EXT = {
    "audio/wav":  "wav",
    "audio/webm": "webm",
    "audio/ogg":  "ogg",
    "audio/mp3":  "mp3",
    "audio/mpeg": "mp3",
    "audio/mp4":  "mp4",
    "audio/m4a":  "m4a",
}


class AudioValidationError(ValueError):
    """Raised when uploaded audio fails validation checks."""
    pass


def validate_audio(audio_bytes: bytes, content_type: str) -> str:
    """
    Validate audio upload — size and format.

    Returns:
        File extension string for the content type (e.g. "wav").
    Raises:
        AudioValidationError with a user-friendly message.
    """
    if len(audio_bytes) == 0:
        raise AudioValidationError("Audio file is empty. Please record again.")

    max_bytes = settings.max_audio_size_bytes
    if len(audio_bytes) > max_bytes:
        raise AudioValidationError(
            f"Audio file is too large ({len(audio_bytes) / 1024 / 1024:.1f} MB). "
            f"Maximum allowed is {settings.MAX_AUDIO_SIZE_MB} MB."
        )

    if content_type not in settings.accepted_audio_format_list:
        raise AudioValidationError(
            f"Unsupported audio format: {content_type}. "
            f"Accepted formats: {', '.join(settings.accepted_audio_format_list)}."
        )

    ext = _MIME_TO_EXT.get(content_type)
    if ext is None:
        raise AudioValidationError(f"Internal: no extension mapping for {content_type}.")

    return ext


# ──────────────────────────────────────────────────────────────────────────────
# TranscriptResult dataclass  (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TranscriptResult:
    transcript: str
    confidence: float
    is_low_confidence: bool       # True → ask patient to repeat; do NOT forward to Gemini
    retry_message: str | None     # Message to surface to patient if low confidence


RETRY_MESSAGE = (
    "Sorry, I couldn't quite understand that. "
    "Could you please speak a bit more clearly and try again?"
)


# ──────────────────────────────────────────────────────────────────────────────
# STT — transcribe_audio  (public signature unchanged)
# ──────────────────────────────────────────────────────────────────────────────

def transcribe_audio(
    audio_bytes: bytes,
    content_type: str,
    sample_rate_hertz: int = 16000,   # Kept for signature compatibility; unused by Whisper
    language_code: str = "en-IN",     # BCP-47 → ISO 639-1 hint passed to Whisper
) -> TranscriptResult:
    """
    Transcribe audio bytes to text using local faster-whisper.
    No network call. No API key required.

    Args:
        audio_bytes:        Raw audio bytes (any format in ACCEPTED_AUDIO_FORMATS).
        content_type:       MIME type (e.g. "audio/wav").
        sample_rate_hertz:  Kept for signature compatibility; Whisper handles this internally.
        language_code:      BCP-47 code (e.g. "en-IN"). Region suffix stripped for Whisper.

    Returns:
        TranscriptResult — check is_low_confidence before forwarding to Gemini.
    Raises:
        AudioValidationError: Audio fails format/size validation.
        RuntimeError:         Whisper model fails to load or transcribe.
    """
    ext = validate_audio(audio_bytes, content_type)

    # Strip region suffix: "en-IN" → "en"
    lang = language_code.split("-")[0] if language_code else "en"

    try:
        import io
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        duration_sec = len(audio) / 1000.0
        
        # If audio is < 0.3s or effectively silent (RMS near 0)
        if duration_sec < 0.3 or audio.rms < 10:
            logger.info("DEBUG: Audio is too short (%.2fs) or near-silent (rms=%s). Skipping STT.", duration_sec, audio.rms)
            return TranscriptResult(
                transcript="",
                confidence=0.0,
                is_low_confidence=True,
                retry_message=(
                    "I couldn't detect any speech. "
                    "Please check your microphone and try again."
                ),
            )
    except Exception as exc:
        logger.warning("Pre-STT pydub audio check failed: %s", exc)

    # Write to a temp file — faster-whisper works best with a real file path
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = _get_whisper_model()

        try:
            # faster-whisper returns a generator of Segment objects + TranscriptionInfo
            segments, info = model.transcribe(
                tmp_path,
                language=None,              # Let Whisper auto-detect the language
                beam_size=5,
                vad_filter=True,            # Silently skip silent regions
                vad_parameters={"min_silence_duration_ms": 500},
            )

            # Materialise segments (generator) and build full transcript + confidence
            all_segments = list(segments)
        except ValueError as e:
            if "max() arg is an empty sequence" in str(e):
                logger.info("faster-whisper returned empty sequence (no detectable speech).")
                all_segments = []
            else:
                raise e

        transcript = " ".join(seg.text.strip() for seg in all_segments).strip()

        logger.info("DEBUG [1/7]: Exact text returned by Whisper immediately after transcription: %r", transcript)

        if not transcript:
            logger.info("DEBUG [2/7]: Whisper returned empty transcript.")
            return TranscriptResult(
                transcript="",
                confidence=0.0,
                is_low_confidence=True,
                retry_message=(
                    "I couldn't detect any speech. "
                    "Please check your microphone and try again."
                ),
            )

        # Compute confidence from avg_logprob across all segments (range: [-∞, 0])
        # Clamp to [-1, 0] and map to [0, 1]
        probs = [getattr(seg, "avg_logprob", 0.0) for seg in all_segments]
        logger.info("DEBUG [3/7]: Whisper segment logprobs: %s", probs)
        
        confidence = _segments_to_confidence(all_segments)
        
        print(f"[STT] Transcription completed")
        print(f"[STT] Transcript length: {len(transcript)}")
        print(f"[STT] Transcript: {repr(transcript)}")
        
        is_low_confidence = confidence < settings.STT_MIN_CONFIDENCE
        
        logger.info("Whisper confidence score calculated: %s (threshold is %s). is_low_confidence=%s", confidence, settings.STT_MIN_CONFIDENCE, is_low_confidence)

        return TranscriptResult(
            transcript=transcript,
            confidence=confidence,
            is_low_confidence=is_low_confidence,
            retry_message=None,
        )

    except Exception as exc:
        logger.error("faster-whisper transcription error: %s", exc)
        raise RuntimeError(
            "Speech recognition failed. Please try typing your response instead."
        ) from exc
    finally:
        # Always clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _segments_to_confidence(segments: list) -> float:
    """
    Convert faster-whisper segment avg_logprob values to a 0–1 confidence score.
    avg_logprob is a log probability (e.g. -0.3). We use math.exp() to get the true probability.
    """
    if not segments:
        return 1.0
    try:
        import math
        probs = [getattr(seg, "avg_logprob", 0.0) for seg in segments]
        avg = sum(probs) / len(probs)
        return round(math.exp(avg), 3)
    except Exception:
        return 1.0


# ──────────────────────────────────────────────────────────────────────────────
# TTS — pyttsx3 (Windows local TTS)
# ──────────────────────────────────────────────────────────────────────────────

def synthesize_speech(
    text: str,
    language_code: str = "en-IN",     
    voice_name: str = "",             
    speaking_rate: float = 0.9,       
) -> bytes:
    """
    Convert text to speech using pyttsx3 (works purely locally without DLLs).
    We initialize the engine per-request because it runs in a threadpool and SAPI5 COM objects are thread-local.
    """
    if not text or not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    if pyttsx3 is None:
        # Optional dependency not installed in this environment. The caller
        # (app.services.ai_service.TTSService / the voice-input endpoint)
        # always treats TTS as best-effort and must not fail the
        # consultation workflow because of this.
        raise RuntimeError(
            "pyttsx3 is not installed. Run: pip install pyttsx3 (and pywin32 on Windows)."
        )

    if len(text) > 4000:
        text = text[:4000] + "..."
        logger.debug("TTS input truncated to 4000 chars.")

    logger.info("[TTS] Starting pyttsx3")

    # `sapi5` only exists on Windows. Using it unconditionally makes TTS
    # fail on every non-Windows deployment (e.g. the Docker/Linux backend
    # described in docker-compose.yml). Pick a driver that actually exists
    # for the current platform instead; pyttsx3 falls back to its own
    # platform default (nsss on macOS, espeak on Linux) when no driver name
    # is given.
    is_windows = platform.system() == "Windows"
    driver_name = "sapi5" if is_windows else None

    try:
        # Crucial for running SAPI5 inside a threadpool! Only relevant/available on Windows.
        if is_windows and pythoncom is not None:
            pythoncom.CoInitialize()

        engine = pyttsx3.init(driver_name)
        logger.info("[TTS] Engine initialized (driver=%s)", driver_name or "platform default")
        
        # speaking_rate < 1.0 means slower. pyttsx3 default is ~200wpm
        rate = engine.getProperty('rate')
        engine.setProperty('rate', int(rate * speaking_rate))

        # Select appropriate voice
        voices = engine.getProperty('voices')
        selected_voice = None
        
        if "ml" in language_code.lower():
            for v in voices:
                langs = getattr(v, "languages", [])
                if any("ml" in lang.lower() for lang in langs) or "malayalam" in v.name.lower():
                    selected_voice = v.id
                    break
            if not selected_voice:
                logger.warning("Malayalam TTS requested, but no compatible Windows Malayalam SAPI voice is installed. Falling back to default English voice.")
        
        if selected_voice:
            engine.setProperty('voice', selected_voice)

    except Exception as exc:
        logger.error("[TTS] Failed to initialize pyttsx3 TTS engine: %s", exc, exc_info=True)
        raise RuntimeError("Failed to initialize pyttsx3 TTS engine.") from exc

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        logger.info("[TTS] Speech synthesis started")
        engine.save_to_file(text, tmp_path)
        
        logger.info("[TTS] before runAndWait")
        engine.runAndWait()
        logger.info("[TTS] after runAndWait")
        
        logger.info("[TTS] Speech synthesis completed")
        
        # Verify file
        if not os.path.exists(tmp_path):
            raise RuntimeError(f"pyttsx3 failed to create audio file at {tmp_path}")
            
        file_size = os.path.getsize(tmp_path)
        if file_size == 0:
            raise RuntimeError(f"pyttsx3 created an empty audio file at {tmp_path}")
            
        logger.info("[TTS] Audio file created (size: %s bytes)", file_size)

        with open(tmp_path, "rb") as f:
            wav_bytes = f.read()
            
        # Convert WAV → MP3 so the response format stays consistent
        return _wav_to_mp3(wav_bytes)
    except Exception as exc:
        logger.error("pyttsx3 TTS synthesis error (REAL ERROR): %s", exc, exc_info=True)
        raise exc
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        if is_windows and pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


def _wav_to_mp3(wav_bytes: bytes) -> bytes:
    """
    Convert raw WAV bytes to MP3 bytes using pydub + ffmpeg.
    ffmpeg must be installed and on PATH.
    Gracefully falls back to returning WAV bytes if ffmpeg is unavailable —
    browsers can play WAV too, so this is non-fatal.
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        mp3_buf = io.BytesIO()
        audio.export(mp3_buf, format="mp3", bitrate="128k")
        return mp3_buf.getvalue()
    except Exception as exc:
        logger.warning(
            "pydub WAV->MP3 conversion failed (%s). Returning WAV bytes instead. "
            "Install ffmpeg to enable MP3 output.", exc,
        )
        return wav_bytes
