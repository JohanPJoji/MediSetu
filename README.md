# MediSetu

MediSetu is an AI-assisted patient intake and clinical workflow prototype built around:

- React + TypeScript frontend
- FastAPI backend
- PostgreSQL
- SQLAlchemy + Alembic
- JWT authentication + RBAC
- provider-agnostic AI/STT/OCR/TTS interfaces

## Repository

```text
frontend/   React/Vite client
backend/    FastAPI + PostgreSQL application
ai/         prompts/schemas shared by AI workflows
docs/       requirements, architecture and current state
```

## Local setup

### 1. PostgreSQL

Create a PostgreSQL database and user matching `DATABASE_URL`, or use:

```bash
docker compose up -d postgres
```

### 2. Backend

From `backend/`:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Set environment variables (see root `.env.example`), including:

```text
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=<long random secret>
```

Apply migrations:

```bash
alembic upgrade head
```

Create the local demo users:

```bash
python -m app.seed_demo
```

Start the API:

```bash
uvicorn app.main:app --reload
```

API documentation:

```text
http://localhost:8000/docs
```

### 3. Frontend

From `frontend/`:

```bash
npm install
npm run dev
```

The Vite development server proxies `/api` to `http://localhost:8000`.

## Demo accounts

The optional `app.seed_demo` command creates local-only demo accounts:

| Role | Email | Password |
|---|---|---|
| Admin | admin@medisetu.dev | Admin@123456 |
| Doctor | doctor@medisetu.dev | Doctor@12345 |
| Pharmacy | pharmacy@medisetu.dev | Pharmacy@12345 |
| Nurse | nurse@medisetu.dev | Nurse@12345 |
| Patient | patient@medisetu.dev | Patient@12345 |

Change these credentials before any shared deployment.

## Safety boundary

The AI is a documentation/decision-support component. It must not independently diagnose, prescribe, change doctor-confirmed records, or modify pharmacy inventory.

External ABHA/HIS/FHIR adapters and AI/STT/OCR/TTS providers may run in mock/development mode until real credentials/providers are configured.

## Verification status

See `docs/CURRENT_STATE.md` for the exact verified/unverified status. This repository should not be considered production-certified clinical software without formal security, privacy, clinical safety, and integration validation.

## Current verification checkpoint

The backend has previously passed the original 49-test suite on the supported local
Python/PostgreSQL environment. The integration pass adds laboratory, billing,
payments, inventory-batch and medicine-alert APIs plus a lightweight React/Vite demo
frontend. Run the backend test suite, Alembic upgrade and frontend production build
again after this integration before treating the repository as release-verified.

## Amal Jyothi feature merge

The integrated project now includes local voice transcription, confidence-gated speech intake, conversational follow-up questions, doctor-facing transcript summaries, optional local TTS responses, and deterministic emergency red-flag handling. These features are implemented on MediSetu's existing PostgreSQL/UUID/RBAC consultation model rather than introducing the Amal project's separate database/auth stack.
