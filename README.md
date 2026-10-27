# MediSetu

MediSetu is an AI-assisted patient intake and clinical workflow platform prototype. It helps patients describe their symptoms, supports doctors in reviewing consultations, and connects clinical workflows with pharmacy and laboratory operations.

## Features

### Patient Consultations
- Create and manage patient consultations.
- Conduct AI-assisted symptom intake through voice input or typed responses.
- Record patient answers and AI follow-up questions in a consultation transcript.
- Track consultation status throughout the intake and review process.
- Submit completed intake information for doctor review.

### AI-Assisted Clinical Workflows
- Generate clinical summaries from consultation information.
- Use conversational follow-up questions to collect relevant symptom details.
- Identify potential emergency red flags and display urgent-care instructions.
- Support speech-to-text transcription through the configured speech recognition provider.
- Provide optional AI-generated medicine suggestions when a supported external LLM provider is configured.

**Important:** AI-generated content is intended to support clinical documentation and review. It must not replace professional medical judgment.

### Doctor Dashboard
- Search for and select patients.
- View a patient's consultation history and status.
- Review consultation transcripts and available clinical information.
- Access AI-assisted clinical summaries.
- Manage consultation review and completion workflows.
- Create prescriptions through the supported prescription workflow.

### Pharmacy Management
- View pharmacy orders generated through the prescription workflow.
- Review prescribed medicines, dosage, frequency, duration, and quantity.
- Track order statuses through the pharmacy workflow.
- Support stock checking and reservation where implemented by the configured backend.

### Laboratory and Referrals
- Access laboratory workflows and manage supported laboratory orders.
- Create and track referrals through the available referral functionality.

### Additional Application Modules
The application also includes backend APIs and frontend modules for:
- Authentication and role-based access control (RBAC)
- Patient and doctor management
- Medicine catalog and inventory
- Inventory batches and medicine alerts
- Billing and payments
- Pharmacy orders and prescriptions

The availability of individual features depends on the implemented API workflows, database configuration, and external service configuration.

## Technology Stack

- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy with asynchronous database access
- **Migrations:** Alembic
- **Authentication:** JWT with role-based access control
- **AI integrations:** Provider-agnostic interfaces for AI, speech-to-text (STT), optical character recognition (OCR), and text-to-speech (TTS)

## Repository Structure

```text
frontend/   React and Vite frontend
backend/    FastAPI backend and database integration
ai/         Shared AI prompts and schemas
docs/       Requirements, architecture, and current-state documentation
```

## Local Setup

### Prerequisites

Install the following before starting:

- Python compatible with the backend dependencies
- Node.js and npm
- PostgreSQL, or Docker with Docker Compose
- Git, if cloning the repository

### 1. Configure PostgreSQL

Create a PostgreSQL database and user matching the `DATABASE_URL` setting in your backend environment.

If the repository's Docker Compose configuration includes a PostgreSQL service, you can start it with:

```bash
docker compose up -d postgres
```

Run this command from the directory containing the relevant `compose.yaml` or `docker-compose.yml` file.

### 2. Set Up the Backend

Open a terminal in the `backend/` directory.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Configure the required environment variables using the repository's environment example and backend configuration. At minimum, configure the database connection and JWT secret.

Example:

```text
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/<database>
JWT_SECRET=<long-random-secret>
```

Use the actual environment variable names expected by the application. Do not commit real secrets to version control.

Apply database migrations:

```bash
alembic upgrade head
```

Create the local demo accounts and associated demo profiles:

```bash
python -m app.seed_demo
```

Start the FastAPI development server:

```bash
python -m uvicorn app.main:app --reload
```

The API should be available at:

- API: `http://localhost:8000`
- Interactive API documentation: `http://localhost:8000/docs`

Keep the backend terminal running while using the frontend.

### 3. Set Up the Frontend

Open a second terminal in the `frontend/` directory.

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

Open the local URL printed by Vite, typically:

`http://localhost:5173`

The frontend is configured to proxy `/api` requests to `http://localhost:8000`. Keep both development servers running.

## Local Demo Accounts

Run `python -m app.seed_demo` from the backend directory to create the following demo accounts.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@medisetu.dev` | `Admin@123456` |
| Doctor | `doctor@medisetu.dev` | `Doctor@12345` |
| Pharmacy | `pharmacy@medisetu.dev` | `Pharmacy@12345` |
| Nurse | `nurse@medisetu.dev` | `Nurse@12345` |
| Patient | `patient@medisetu.dev` | `Patient@12345` |

These credentials are for local development and demonstration only. Change them before any shared or deployed use.

The seed script skips demo users that already exist. If a database already contains users, running the script again will not necessarily reset their passwords or repair every existing profile.

## AI and External Services

AI, speech recognition, OCR, and text-to-speech functionality depend on the providers and settings configured in the backend.

If the application uses a mock AI provider, external-provider features may return limited results or no generated suggestions. Configure a supported provider and its credentials if external AI functionality is required.

Do not assume that a feature is fully operational simply because its interface is visible. Verify the relevant backend configuration and API workflow.

## Safety and Security

MediSetu is a prototype, not certified clinical software.

- AI output must be reviewed by a qualified healthcare professional.
- The system must not independently diagnose patients, issue doctor-confirmed prescriptions, or override clinical decisions.
- Prescription creation, pharmacy inventory changes, and other clinical actions must follow the application's authorization and validation rules.
- External healthcare integrations may be unavailable or operate in development/mock mode.
- Demo credentials must never be used in a production deployment.
- Production use requires appropriate security testing, privacy safeguards, access-control validation, clinical safety review, and integration testing.

## Verification

Refer to `docs/CURRENT_STATE.md` for the project's documented implementation and verification status.

After making changes, validate the backend tests, database migrations, and frontend production build before treating the project as release-ready.

Typical validation commands are:

**Backend** — run from `backend/` with the virtual environment activated:

```bash
python -m pytest
alembic upgrade head
```

**Frontend** — run from `frontend/`:

```bash
npx tsc --noEmit
npm run build
```

A successful build or passing test suite does not, by itself, establish production readiness or clinical safety.
