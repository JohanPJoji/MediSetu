# MediSetu — AI Module

This directory is reserved for AI-related assets: prompt templates
(`prompts/`) and structured-output schemas (`schemas/`) used by the
conversational intake engine, clinical extraction, and document OCR
pipeline described in `ARCHITECTURE.md` (§17–§28, §42–§44).

**Status: not yet implemented.** This is Phase 5 ("AI Intake") and later
work per `ARCHITECTURE.md` §102. Nothing in this directory is consumed by
the backend yet — `backend/app/core/config.py` already declares the
`LLM_PROVIDER` / `STT_PROVIDER` / `OCR_PROVIDER` / `TTS_PROVIDER` environment
variables so this phase can be added without reshaping configuration.

See `docs/CURRENT_STATE.md` for the current implementation phase.
