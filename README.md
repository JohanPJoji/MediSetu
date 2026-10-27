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

### 
