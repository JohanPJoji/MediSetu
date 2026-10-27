"""
Application configuration.

Per ARCHITECTURE.md §60 (CONFIGURATION):
- All configuration must come from environment variables.
- Secrets must never be hard-coded or committed.
- A `.env.example` at the repo root documents every variable.

This module defines the full configuration surface described in
ARCHITECTURE.md, including variables for AI/STT/OCR/TTS/ABHA/HIS providers
that are not yet used by any Phase 1 code. They are declared now (with safe
defaults of None/"" ) so that:
  1. The `.env.example` contract is visible and stable from the start.
  2. Later phases (5, 7, 11, ...) can start consuming them without having
     to re-touch this file's shape.

Phase 1 only actually reads: DATABASE_URL, ENVIRONMENT, APP_NAME,
API_V1_PREFIX, LOG_LEVEL. Everything else is inert until its owning phase
is implemented.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    """Central application settings, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Core application ---
    APP_NAME: str = "MediSetu Backend"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"

    # --- Database (Phase 1) ---
    # Async SQLAlchemy + asyncpg expects the "postgresql+asyncpg://" scheme.
    DATABASE_URL: str

    # --- Authentication (Phase 2 — declared now, not yet used) ---
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- AI providers (Phase 5 — declared now, not yet used) ---
    LLM_PROVIDER: Optional[str] = None
    LLM_API_KEY: Optional[str] = None

    STT_PROVIDER: Optional[str] = None
    STT_API_KEY: Optional[str] = None

    TTS_PROVIDER: Optional[str] = None
    TTS_API_KEY: Optional[str] = None
    TTS_VOICE: str = "en-US"

    # Local speech-to-text / audio settings.
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_MODEL_DIR: Optional[str] = None
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    MAX_AUDIO_SIZE_MB: int = 10
    ACCEPTED_AUDIO_FORMATS: str = "audio/wav,audio/webm,audio/ogg,audio/mp3,audio/mpeg,audio/mp4,audio/m4a"
    STT_MIN_CONFIDENCE: float = 0.65

    OCR_PROVIDER: Optional[str] = None
    OCR_API_KEY: Optional[str] = None
    MOCK_TRANSCRIPT: Optional[str] = None

    # Optional OpenAI-compatible LLM provider (Omni Router supported).
    # Leave unset to preserve MediSetu's deterministic local behavior.
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    LLM_TIMEOUT_SECONDS: int = 20

    # --- External integrations (Phase 11 — declared now, not yet used) ---
    ABHA_BASE_URL: Optional[str] = None
    ABHA_CLIENT_ID: Optional[str] = None
    ABHA_CLIENT_SECRET: Optional[str] = None

    HIS_BASE_URL: Optional[str] = None
    HIS_API_KEY: Optional[str] = None


    @property
    def accepted_audio_format_list(self) -> list[str]:
        return [f.strip() for f in self.ACCEPTED_AUDIO_FORMATS.split(",") if f.strip()]

    @property
    def max_audio_size_bytes(self) -> int:
        return self.MAX_AUDIO_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-parsing env on every call)."""
    return Settings()
