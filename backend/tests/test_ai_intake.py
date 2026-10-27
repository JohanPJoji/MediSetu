import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

async def _register_and_login(client: AsyncClient, *, role: str, prefix: str) -> str:
    email = _unique_email(prefix)
    password = "correct-horse-9"
    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": f"{prefix} User", "role": role},
    )
    assert reg.status_code == 201, reg.text
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

@pytest.mark.asyncio
async def test_ai_intake_workflow(client: AsyncClient) -> None:
    # Setup Patient and Consultation
    pat_token = await _register_and_login(client, role="PATIENT", prefix="ai_pat")
    patient_id = await _create_patient(client, pat_token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(pat_token))
    c_id = create_res.json()["data"]["id"]

    # 1. Add transcript entry
    trans_res = await client.post(f"/api/consultations/{c_id}/transcript", json={"role": "PATIENT", "content": "I have severe chest pain"}, headers=_auth(pat_token))
    assert trans_res.status_code == 201

    # 2. Process intake
    process_res = await client.post(f"/api/consultations/{c_id}/process-intake", headers=_auth(pat_token))
    assert process_res.status_code == 200
    
    body = process_res.json()
    assert body["success"] is True
    assert "clinical_history" in body["data"]
    assert body["data"]["triage_alert"] is True  # Because our mock LLM returns "Severe chest pain" in red_flags

    # 3. Get Clinical History
    get_res = await client.get(f"/api/consultations/{c_id}/clinical-history", headers=_auth(pat_token))
    assert get_res.status_code == 200
    assert get_res.json()["data"]["chief_complaint"] == "Chest pain"
