"""
Tests for Phase 3 — Patient.

Per ARCHITECTURE.md §76 (TESTING STRATEGY) and §12 (ROLE-BASED ACCESS
CONTROL): this module exercises Patient profile creation, own-profile
read/update, duplicate-profile rejection, validation errors, and the RBAC
rules from §12 — most importantly the explicit "cannot access another
patient" requirement.

Same conventions as tests/test_auth.py: real HTTP calls via
`httpx.AsyncClient` against the real app + real Postgres database, unique
emails per test, no teardown (see test_auth.py's module docstring for why
this is an accepted prototype-phase tradeoff).
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def _valid_patient_payload(**overrides) -> dict:
    payload = {
        "name": "Test Patient",
        "date_of_birth": "1990-05-15",
        "sex": "FEMALE",
        "contact_information": "+91-9000000000",
        "preferred_language": "en",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_and_login(client: AsyncClient, *, role: str, prefix: str) -> str:
    """Create a test user and return a bearer token.

    Public API registration is intentionally PATIENT-only. Staff/admin test
    users are created through the same direct persistence path used by the
    authentication tests, rather than weakening the production registration
    security boundary just to satisfy fixtures.
    """
    email = _unique_email(prefix)
    password = "correct-horse-9"
    if role == "PATIENT":
        reg = await client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": f"{prefix} User", "role": role},
        )
        assert reg.status_code == 201, reg.text
    else:
        async with AsyncSessionLocal() as db:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=f"{prefix} User",
                role=UserRole(role),
                is_active=True,
            )
            db.add(user)
            await db.commit()
    login = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["data"]["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Create own profile ------------------------------------------------


@pytest.mark.asyncio
async def test_patient_can_create_own_profile(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="create")

    response = await client.post(
        "/api/patients", json=_valid_patient_payload(), headers=_auth(token)
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Test Patient"
    assert body["data"]["sex"] == "FEMALE"
    assert body["data"]["date_of_birth"] == "1990-05-15"
    assert "age" in body["data"]
    assert isinstance(body["data"]["age"], int)
    assert body["data"]["abha_id"] is None


@pytest.mark.asyncio
async def test_create_profile_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/patients", json=_valid_patient_payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


@pytest.mark.asyncio
async def test_only_patient_role_can_create_profile(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="DOCTOR", prefix="docnotpatient")

    response = await client.post(
        "/api/patients", json=_valid_patient_payload(), headers=_auth(token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_creating_second_profile_for_same_user_rejected(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="dupprofile")

    first = await client.post(
        "/api/patients", json=_valid_patient_payload(), headers=_auth(token)
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/patients", json=_valid_patient_payload(name="Other Name"), headers=_auth(token)
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "PATIENT_PROFILE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_profile_rejects_future_date_of_birth(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="futuredob")
    future_dob = (date.today() + timedelta(days=30)).isoformat()

    response = await client.post(
        "/api/patients",
        json=_valid_patient_payload(date_of_birth=future_dob),
        headers=_auth(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_profile_rejects_invalid_sex(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="badsex")

    response = await client.post(
        "/api/patients", json=_valid_patient_payload(sex="UNKNOWN"), headers=_auth(token)
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# --- Read/update own profile --------------------------------------------


@pytest.mark.asyncio
async def test_get_me_returns_404_before_profile_created(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="nome")

    response = await client.get("/api/patients/me", headers=_auth(token))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_patient_can_read_own_profile(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="readown")
    await client.post("/api/patients", json=_valid_patient_payload(), headers=_auth(token))

    response = await client.get("/api/patients/me", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Test Patient"


@pytest.mark.asyncio
async def test_patient_can_update_own_profile(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="updateown")
    await client.post("/api/patients", json=_valid_patient_payload(), headers=_auth(token))

    response = await client.patch(
        "/api/patients/me",
        json={"name": "Updated Name", "preferred_language": "hi"},
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["name"] == "Updated Name"
    assert body["data"]["preferred_language"] == "hi"
    # Unspecified fields are left untouched.
    assert body["data"]["sex"] == "FEMALE"


@pytest.mark.asyncio
async def test_update_rejects_empty_body(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="emptyupdate")
    await client.post("/api/patients", json=_valid_patient_payload(), headers=_auth(token))

    response = await client.patch("/api/patients/me", json={}, headers=_auth(token))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# --- RBAC: patients cannot access other patients' records ---------------


@pytest.mark.asyncio
async def test_patient_cannot_access_another_patient_by_id(client: AsyncClient) -> None:
    victim_token = await _register_and_login(client, role="PATIENT", prefix="victim")
    victim_create = await client.post(
        "/api/patients", json=_valid_patient_payload(), headers=_auth(victim_token)
    )
    victim_patient_id = victim_create.json()["data"]["id"]

    attacker_token = await _register_and_login(client, role="PATIENT", prefix="attacker")

    response = await client.get(
        f"/api/patients/{victim_patient_id}", headers=_auth(attacker_token)
    )

    # A PATIENT-role token is forbidden from this route entirely, regardless
    # of whose id is requested — see app/api/patients.py's module docstring.
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_doctor_can_read_patient_by_id(client: AsyncClient) -> None:
    patient_token = await _register_and_login(client, role="PATIENT", prefix="fordoc")
    created = await client.post(
        "/api/patients", json=_valid_patient_payload(), headers=_auth(patient_token)
    )
    patient_id = created.json()["data"]["id"]

    doctor_token = await _register_and_login(client, role="DOCTOR", prefix="doclookup")
    doctor_me = await client.get("/api/users/me", headers=_auth(doctor_token))
    assert doctor_me.status_code == 200, doctor_me.text
    doctor_id = doctor_me.json()["data"]["id"]

    # A doctor may access a patient's record only when assigned to a real
    # consultation for that patient.
    consultation = await client.post(
        "/api/consultations",
        json={"patient_id": patient_id},
        headers=_auth(patient_token),
    )
    assert consultation.status_code == 201, consultation.text
    consultation_id = consultation.json()["data"]["id"]
    assignment = await client.patch(
        f"/api/consultations/{consultation_id}/assign",
        json={"doctor_id": doctor_id},
        headers=_auth(doctor_token),
    )
    assert assignment.status_code == 200, assignment.text

    response = await client.get(f"/api/patients/{patient_id}", headers=_auth(doctor_token))

    assert response.status_code == 200
    assert response.json()["data"]["id"] == patient_id


@pytest.mark.asyncio
async def test_get_patient_by_id_404_for_unknown_id(client: AsyncClient) -> None:
    doctor_token = await _register_and_login(client, role="DOCTOR", prefix="doc404")

    response = await client.get(f"/api/patients/{uuid.uuid4()}", headers=_auth(doctor_token))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_NOT_FOUND"


# --- List all patients: ADMIN only ---------------------------------------


@pytest.mark.asyncio
async def test_list_patients_forbidden_for_non_admin(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="DOCTOR", prefix="listnonadmin")

    response = await client.get("/api/patients", headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_list_patients_allowed_for_admin(client: AsyncClient) -> None:
    patient_token = await _register_and_login(client, role="PATIENT", prefix="forlist")
    created = await client.post(
        "/api/patients", json=_valid_patient_payload(), headers=_auth(patient_token)
    )
    patient_id = created.json()["data"]["id"]

    admin_token = await _register_and_login(client, role="ADMIN", prefix="listadmin")

    response = await client.get("/api/patients", headers=_auth(admin_token))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert any(p["id"] == patient_id for p in body["data"])
