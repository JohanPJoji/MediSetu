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

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

async def _register_and_login(client: AsyncClient, *, role: str, prefix: str) -> str:
    """Create a test user and return a bearer token.

    Public API registration is intentionally PATIENT-only. Staff/admin test
    users are created directly so tests exercise the privileged workflows
    without weakening the production signup boundary.
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

async def _create_patient(client: AsyncClient, token: str) -> str:
    response = await client.post(
        "/api/patients", 
        json={
            "name": "Test Patient",
            "date_of_birth": "1990-05-15",
            "sex": "FEMALE",
            "contact_information": "+91-9000000000",
            "preferred_language": "en",
        }, 
        headers=_auth(token)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


# --- Creation and RBAC ---

@pytest.mark.asyncio
async def test_patient_can_create_consultation(client: AsyncClient) -> None:
    token = await _register_and_login(client, role="PATIENT", prefix="ccons")
    patient_id = await _create_patient(client, token)

    response = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(token))
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "CREATED"
    assert body["data"]["doctor_id"] is None

@pytest.mark.asyncio
async def test_patient_cannot_create_for_another(client: AsyncClient) -> None:
    victim_token = await _register_and_login(client, role="PATIENT", prefix="victim")
    victim_id = await _create_patient(client, victim_token)

    attacker_token = await _register_and_login(client, role="PATIENT", prefix="attacker")
    await _create_patient(client, attacker_token)

    response = await client.post("/api/consultations", json={"patient_id": victim_id}, headers=_auth(attacker_token))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"

@pytest.mark.asyncio
async def test_patient_cannot_view_another_consultation(client: AsyncClient) -> None:
    victim_token = await _register_and_login(client, role="PATIENT", prefix="vview")
    victim_id = await _create_patient(client, victim_token)
    create_res = await client.post("/api/consultations", json={"patient_id": victim_id}, headers=_auth(victim_token))
    c_id = create_res.json()["data"]["id"]

    attacker_token = await _register_and_login(client, role="PATIENT", prefix="aview")
    await _create_patient(client, attacker_token)

    response = await client.get(f"/api/consultations/{c_id}", headers=_auth(attacker_token))
    assert response.status_code == 403


# --- Doctor Assignment and Access ---

@pytest.mark.asyncio
async def test_doctor_cannot_view_unassigned_consultation(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_unassigned")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    doc_token = await _register_and_login(client, role="DOCTOR", prefix="doc_unassigned")
    response = await client.get(f"/api/consultations/{c_id}", headers=_auth(doc_token))
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_doctor_can_assign_unassigned_to_themselves(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_assign")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    doc_token = await _register_and_login(client, role="DOCTOR", prefix="doc_assign")
    # We need the doctor's own ID
    me_res = await client.get("/api/users/me", headers=_auth(doc_token))
    doc_id = me_res.json()["data"]["id"]

    assign_res = await client.patch(f"/api/consultations/{c_id}/assign", json={"doctor_id": doc_id}, headers=_auth(doc_token))
    assert assign_res.status_code == 200
    assert assign_res.json()["data"]["doctor_id"] == doc_id

    # Now they can view it
    view_res = await client.get(f"/api/consultations/{c_id}", headers=_auth(doc_token))
    assert view_res.status_code == 200

@pytest.mark.asyncio
async def test_doctor_cannot_assign_to_another_doctor(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_reassign")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    doc_token = await _register_and_login(client, role="DOCTOR", prefix="doc_reassign")
    other_doc_id = str(uuid.uuid4())

    assign_res = await client.patch(f"/api/consultations/{c_id}/assign", json={"doctor_id": other_doc_id}, headers=_auth(doc_token))
    assert assign_res.status_code == 403

# --- State Transitions ---

@pytest.mark.asyncio
async def test_valid_state_transitions(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_state")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    # Admin to drive the states
    admin_token = await _register_and_login(client, role="ADMIN", prefix="admin_state")

    # CREATED -> IN_PROGRESS
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "IN_PROGRESS"}, headers=_auth(pat_token))
    assert res.status_code == 200

    # IN_PROGRESS -> AI_PROCESSING
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "AI_PROCESSING"}, headers=_auth(admin_token))
    assert res.status_code == 200

    # AI_PROCESSING -> UNDER_REVIEW
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "UNDER_REVIEW"}, headers=_auth(admin_token))
    assert res.status_code == 200

    # UNDER_REVIEW -> APPROVED
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "APPROVED"}, headers=_auth(admin_token))
    assert res.status_code == 200

    # APPROVED -> COMPLETED
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "COMPLETED"}, headers=_auth(admin_token))
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_invalid_state_transition(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_inv")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    admin_token = await _register_and_login(client, role="ADMIN", prefix="admin_inv")

    # CREATED -> COMPLETED (Invalid)
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "COMPLETED"}, headers=_auth(admin_token))
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_patient_can_only_start_and_cancel(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_cancel")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    # Try AI_PROCESSING
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "AI_PROCESSING"}, headers=_auth(pat_token))
    assert res.status_code == 403

    # Try IN_PROGRESS
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "IN_PROGRESS"}, headers=_auth(pat_token))
    assert res.status_code == 200

    # Try CANCELLED
    res = await client.patch(f"/api/consultations/{c_id}/status", json={"status": "CANCELLED"}, headers=_auth(pat_token))
    assert res.status_code == 200

# --- Transcript Tests ---

@pytest.mark.asyncio
async def test_transcript_creation_and_retrieval(client: AsyncClient) -> None:
    pat_token = await _register_and_login(client, role="PATIENT", prefix="pat_ts")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    res = await client.post(f"/api/consultations/{c_id}/transcript", json={"role": "PATIENT", "content": "I have a headache"}, headers=_auth(pat_token))
    assert res.status_code == 201
    assert res.json()["data"]["content"] == "I have a headache"

    # Retrieve
    get_res = await client.get(f"/api/consultations/{c_id}/transcript", headers=_auth(pat_token))
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 1
    assert get_res.json()["data"][0]["content"] == "I have a headache"
