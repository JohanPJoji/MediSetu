# MediSetu Backend

FastAPI backend for MediSetu. Currently implements **Phase 1 — Foundation**
only (see `../docs/CURRENT_STATE.md` for exact status): app skeleton,
configuration, async SQLAlchemy + PostgreSQL wiring, Alembic migrations,
a `/health` endpoint, logging, and a pytest test suite. No domain models,
auth, or business features are implemented yet — those begin at Phase 2.

## Prerequisites

- Python 3.11+ (developed against 3.12)
- PostgreSQL 14+ — either:
  - a locally installed PostgreSQL server, **or**
  - the `postgres` service in the repo-root `docker-compose.yml`

## 1. Configure environment variables

From the repo root:

```bash
cp .env.example backend/.env
```

Adjust `DATABASE_URL` in `backend/.env` if your local Postgres isn't using
the default `medisetu` / `medisetu_dev_password` credentials on `localhost:5432`.

## 2. Install dependencies

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 3. Provide a database

**Option A — local PostgreSQL install:**

```bash
sudo -u postgres psql -c "CREATE USER medisetu WITH PASSWORD 'medisetu_dev_password';"
sudo -u postgres psql -c "CREATE DATABASE medisetu OWNER medisetu;"
```

**Option B — Docker Compose (from repo root):**

```bash
docker compose up -d postgres
```

Either way, `DATABASE_URL` in `backend/.env` should point at whichever one
you're using (`localhost` for a local install, `postgres` as the host if
running the backend itself inside Docker Compose — see the compose file's
`backend` service for that override).

## 4. Run database migrations

```bash
cd backend
.venv/bin/alembic upgrade head
```

## 5. Run the backend

```bash
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's up:

```bash
curl http://localhost:8000/health
# {"success":true,"data":{"status":"ok","database":"ok"},"message":null}
```

Interactive API docs: http://localhost:8000/docs

## 6. Run tests

```bash
.venv/bin/python -m pytest -v
```

## Creating new migrations

After adding/changing a model under `app/models/` (imported into
`app/database/migrations/env.py`):

```bash
.venv/bin/alembic revision --autogenerate -m "describe the change"
.venv/bin/alembic upgrade head
```

## Authentication (Phase 2)

```bash
# Register (role is PATIENT | DOCTOR | PHARMACY | NURSE | ADMIN)
curl -X POST localhost:8000/api/auth/register -H "Content-Type: application/json" \
  -d '{"email":"doc@example.com","password":"a-strong-password","full_name":"Dr. Example","role":"DOCTOR"}'

# Login
curl -X POST localhost:8000/api/auth/login -H "Content-Type: application/json" \
  -d '{"email":"doc@example.com","password":"a-strong-password"}'
# -> {"success":true,"data":{"access_token":"...","token_type":"bearer"},"message":null}

# Authenticated request
curl localhost:8000/api/users/me -H "Authorization: Bearer <access_token>"

# Admin-only request (any non-admin token gets 403)
curl localhost:8000/api/users -H "Authorization: Bearer <admin_access_token>"
```

## Patients (Phase 3)

```bash
# Create your own patient profile (PATIENT role only; one per account)
curl -X POST localhost:8000/api/patients -H "Content-Type: application/json" \
  -H "Authorization: Bearer <patient_access_token>" \
  -d '{"name":"Asha Patient","date_of_birth":"1990-05-15","sex":"FEMALE","contact_information":"+91-9000000000","preferred_language":"hi"}'

# Read your own profile
curl localhost:8000/api/patients/me -H "Authorization: Bearer <patient_access_token>"

# Partially update your own profile
curl -X PATCH localhost:8000/api/patients/me -H "Content-Type: application/json" \
  -H "Authorization: Bearer <patient_access_token>" \
  -d '{"preferred_language":"en"}'

# Doctor/Nurse/Admin: look up any patient by id (a PATIENT token gets 403 here)
curl localhost:8000/api/patients/<patient_id> -H "Authorization: Bearer <doctor_access_token>"

# Admin-only: list all patients
curl localhost:8000/api/patients -H "Authorization: Bearer <admin_access_token>"
```

## Project layout

See `../docs/ARCHITECTURE.md` §9 for the authoritative repository structure.
This backend follows it: `app/api`, `app/core`, `app/database`, `app/models`,
`app/schemas`, `app/services`, `app/middleware`, `app/utils`, `tests/`.
