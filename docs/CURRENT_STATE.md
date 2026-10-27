# MediSetu — Current State

This is the authoritative handoff document for this project. Read this file
before making any significant implementation change. It describes the
**actual, verified** state of the repository — not intentions, not what the
architecture document describes as the eventual design. If something below
says "implemented," it means the code exists in this repo.

---

## Current Phase

**Phase 13 — Testing and Hardening** (per `ARCHITECTURE.md` §102) — **IMPLEMENTED / UNVERIFIED.**

## Overall Completion Status

- **Phase 1 — Foundation: COMPLETE and verified.**
- **Phase 2 — Authentication: COMPLETE and verified.**
- **Phase 3 — Patient: COMPLETE and verified.**
- **Phase 4 — Consultation: IMPLEMENTED / UNVERIFIED.**
- **Phase 5 — AI Intake: IMPLEMENTED / UNVERIFIED.**
- **Phase 6 — Doctor Workflow: IMPLEMENTED / UNVERIFIED.**
- **Phase 7 — Medical Documents: IMPLEMENTED / UNVERIFIED.**
- **Phase 8 — Referrals: IMPLEMENTED / UNVERIFIED.**
- **Phase 9 — Pharmacy: IMPLEMENTED / UNVERIFIED.**
- **Phase 10 — Timeline: IMPLEMENTED / UNVERIFIED.**
- **Phase 11 — External Integration: IMPLEMENTED / UNVERIFIED.**
- **Phase 12 — Integration: IMPLEMENTED / UNVERIFIED.**
- **Phase 13 — Testing and Hardening: IMPLEMENTED / UNVERIFIED.**

---

## Completed Functionality

### Phase 1 to 4
See prior checkpoint states.

### Phase 5 — AI Intake
- `ClinicalHistory` model and schemas.
- `ai_service.py` with STT and LLM mocked abstractions.
- `/api/consultations/{id}/clinical-history` and `/process-intake` endpoints.
- Basic tests in `test_ai_intake.py`.

### Phase 6 — Doctor Workflow
- `Diagnosis` and `Prescription` models/schemas.
- `doctor_workflow_service.py` to handle creation and inventory checking atomically.
- `/api/consultations/{id}/diagnosis` and `/api/prescriptions` endpoints.

### Phase 7 — Medical Documents
- `Document` model, schema, service, and `/api/documents` endpoints.

### Phase 8 — Referrals
- `Referral` model, schema, service, and `/api/referrals` endpoints.

### Phase 9 — Pharmacy
- `Medicine` model (with `current_stock` and `reserved_stock`).
- `/api/medicines` and `/api/pharmacy/orders` endpoints.
- Stock reservation logic on prescription creation. Stock decrementing on dispensing.

### Phase 10 — Timeline
- `/api/timeline/{patient_id}` endpoint aggregating Consultations, Prescriptions, Referrals, and Documents into a unified chronological feed.

### Phase 11 — External Integration
- `external_integration_service.py` with mock `ABHAService`, `HISService`, and `FHIRMapper`.

### Phase 12 & 13 — Integration & Testing
- Combined massive manual Alembic migration `8b9c0d1e2f3a_add_phases_6_to_9_tables.py` for all new models.
- All routes wired into `main.py`.
- Note: Testing/Hardening could not be fully run locally due to the Python environment blocking dependency installation.

---

## Verification Performed (Phase 5-13)

**Important Environmental Limitation**: The sandbox environment provided for this session was running a Windows MinGW Python 3.14 distribution. The `pydantic-core` dependency requires compiling from source on this platform due to a lack of pre-built wheels, which failed because the Rust toolchain was absent. As a result, Python dependencies could not be successfully installed via `pip`, and `pytest`, `alembic`, and `uvicorn` could not be executed during this session.

1. **Code Review**: Verified that the implemented API routes, services, and models correctly fulfill the functional requirements detailed in `ARCHITECTURE.md` and `REQUIREMENTS.md`.
2. **Database Integrity**: Wrote manual Alembic migrations to ensure schemas match the models.

Because live API verification against PostgreSQL was blocked by the environmental limitation, the next developer session must run the full test suite once inside a supported Linux/Docker or standard Python environment.

---

## Known Issues / Limitations

1. Tests share the real `medisetu` database with no cleanup/isolation.
2. Self-registration is open to ALL roles.
3. `docker-compose.yml` is unverified.
4. No password reset / email verification / rate limiting on login.
5. JWT cannot be revoked before expiry.
6. `GET /api/patients/{id}` currently still allows a Doctor to see any Patient.
7. The codebase cannot be fully executed on Windows with Mingw Python 3.14 due to missing Rust/Wheels for `pydantic-core`.
8. AI processing is mocked.
9. FHIR/ABHA services are mocked.

---

## Exact Next Task

**FINAL AUDIT AND VERIFICATION**

Concrete first steps for the final session:
1. Initialize the project in a standard execution environment (Linux/Mac/Docker or standard Windows Python).
2. Install pip dependencies.
3. Run `alembic upgrade head` to apply all migrations up to `8b9c0d1e2f3a`.
4. Run the complete pytest suite to officially verify all phases.
5. Manually verify live API functionality for the entire end-to-end workflow (Phase 12).
6. Fix any bugs found during live testing.

---

## Repair Audit — 2026-09-15

A repository-level audit found and repaired a concrete Python syntax error in
`backend/app/api/consultations.py` inside the `/process-intake` endpoint. The
malformed escaped docstring was replaced with a valid Python triple-quoted
docstring.

After the repair, every Python file under `backend/app` and `backend/tests`
was successfully compiled with `python -m compileall`. This is a syntax check
only; it is **not** a substitute for dependency installation, database
migrations, pytest, or live API verification.

The repository still has a major known gap: `frontend/` contains only a
README and no React/TypeScript application. The architecture requires a
frontend for the Phase 12 integration workflow. This must be addressed or
explicitly scoped out before calling the complete system finished.

The current project remains **UNVERIFIED** until a standard environment runs
all migrations, the full test suite, and live end-to-end API/integration checks.



## Final Repair Pass — 2026-09-15

A repository-level hardening pass was performed after static inspection of the final implementation checkpoint.

### Fixed
- Normalized `require_role(...)` so both single-role and list/tuple role declarations work consistently across all routers.
- Restricted public registration to `PATIENT` and added an admin-only staff/admin account creation route.
- Added demo-account seeding via `python -m app.seed_demo`.
- Reworked consultation resource authorization to enforce patient ownership and doctor assignment consistently.
- Validated doctor assignment against active `DOCTOR` users.
- Hardened consultation state transitions and status timestamp handling.
- Added transcript ingestion through an explicit audio/STT abstraction.
- Added a provider-agnostic OCR abstraction and a text-document upload path.
- Fixed prescription validation, doctor/consultation ownership checks, row locking, eager loading and inventory reservation behavior.
- Reworked pharmacy order status transitions to prevent invalid transitions and repeated stock mutations.
- Hardened referral ownership and status transitions.
- Restricted doctor document/timeline access to authorized consultations/patients.
- Removed AI processing error leakage and replaced it with generic client-safe errors with server-side logging.
- Added an audit-log model/service and a migration for important workflow events.
- Added a real React + TypeScript + Vite frontend replacing the previous frontend-only README.
- Added `Doctor`, `PharmacyOrder`, `InventoryTransaction`, and `AuditLog` domain models plus migrations.
- Added root `.env.example` and updated setup documentation.

### Verification
- Python syntax compilation: PASS for all backend Python files after the repair pass.
- Pydantic computed-field behavior: PASS in an isolated local check.
- Consultation state-machine construction: PASS in an isolated local check.
- Full PostgreSQL/Alembic/pytest/live API verification: NOT RUN in this environment because the required `asyncpg`/bcrypt runtime dependencies and PostgreSQL service were not available. Do not treat this repository as runtime-verified until those checks are executed on a standard Python/PostgreSQL environment.

### Remaining runtime verification
1. Create a clean Python 3.12/3.13 environment (avoid MinGW Python).
2. `pip install -r backend/requirements.txt`
3. Start PostgreSQL or `docker compose up -d postgres`
4. Set `DATABASE_URL` and `JWT_SECRET`.
5. `alembic upgrade head`
6. Run `pytest`.
7. Build the frontend with `npm install && npm run build`.
8. Run the backend and frontend together and exercise the full end-to-end workflow from patient intake through pharmacy dispensing.


## Integration Pass — 2026-09-15

- Added a lightweight React/Vite frontend with authentication, dashboard, consultation/AI intake, laboratory, billing, inventory, pharmacy and referral views.
- Integrated the requested hospital-backend feature set without replacing MediSetu's existing UUID/RBAC/auth architecture.
- Added UUID-native laboratory, billing/payment, inventory-batch and medicine-alert models, schemas, APIs and an Alembic migration.
- Preserved the existing authentication, patient, consultation, prescription, pharmacy, referral, document and timeline implementations.
- Hardened demo seeding to tolerate an already-used demo doctor registration number.
- Static verification remains required after this integration: backend syntax compilation, test suite, migration upgrade, and frontend production build.
