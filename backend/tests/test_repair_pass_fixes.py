"""Regression tests for the 2026-09-16 consultation-workflow repair pass.

These cover two concrete bugs found while tracing the voice-first patient
consultation flow:

1. Emergency/safety detection previously only ran on the /voice-input path.
   A typed transcript entry (the documented typing fallback) skipped the
   safety pipeline entirely. See app.api.consultations._flag_emergency_if_needed.

2. The deterministic (no-external-LLM) structured-history fallback never
   populated `severity`/`duration`/`character`, so explicit statements like
   "moderate pain" were dropped from the resulting clinical information, and
   follow-up questions about those fields could never be satisfied. See
   app.services.ai_service._extract_severity/_extract_duration/_extract_character.
"""

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


async def _register_and_login(client: AsyncClient, *, prefix: str) -> str:
    email = _unique_email(prefix)
    password = "correct-horse-9"
    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": f"{prefix} User", "role": "PATIENT"},
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
            "name": "Repair Pass Patient",
            "date_of_birth": "1992-01-01",
            "sex": "FEMALE",
            "contact_information": "+91-9000000001",
            "preferred_language": "en",
        },
        headers=_auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


@pytest.mark.asyncio
async def test_typed_transcript_entry_triggers_same_safety_pipeline_as_voice(client: AsyncClient) -> None:
    """A typed emergency message must be flagged exactly like a voice one."""
    token = await _register_and_login(client, prefix="safety_typed")
    patient_id = await _create_patient(client, token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(token))
    c_id = create_res.json()["data"]["id"]

    res = await client.post(
        f"/api/consultations/{c_id}/transcript",
        json={"role": "PATIENT", "content": "I have crushing chest pain and can't breathe"},
        headers=_auth(token),
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["is_emergency"] is True
    assert data["emergency_instructions"]

    # The fixed emergency message must also be visible to anyone reading the
    # transcript afterwards (a doctor opening the consultation later), not
    # just in the immediate API response.
    transcript_res = await client.get(f"/api/consultations/{c_id}/transcript", headers=_auth(token))
    roles_and_content = [(e["role"], e["content"]) for e in transcript_res.json()["data"]]
    assert ("SYSTEM", data["emergency_instructions"]) in roles_and_content


@pytest.mark.asyncio
async def test_typed_transcript_non_emergency_is_not_flagged(client: AsyncClient) -> None:
    token = await _register_and_login(client, prefix="safety_typed_ok")
    patient_id = await _create_patient(client, token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(token))
    c_id = create_res.json()["data"]["id"]

    res = await client.post(
        f"/api/consultations/{c_id}/transcript",
        json={"role": "PATIENT", "content": "I have a mild headache since yesterday"},
        headers=_auth(token),
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["is_emergency"] is False
    assert data["emergency_instructions"] is None


@pytest.mark.asyncio
async def test_severity_and_duration_are_preserved_in_clinical_history(client: AsyncClient) -> None:
    """'mild/moderate/severe pain' style statements must survive into the
    structured clinical history, not just the raw transcript text."""
    token = await _register_and_login(client, prefix="severity")
    patient_id = await _create_patient(client, token)
    create_res = await client.post("/api/consultations", json={"patient_id": patient_id}, headers=_auth(token))
    c_id = create_res.json()["data"]["id"]

    await client.post(
        f"/api/consultations/{c_id}/transcript",
        json={"role": "PATIENT", "content": "I have a headache"},
        headers=_auth(token),
    )
    await client.post(
        f"/api/consultations/{c_id}/transcript",
        json={"role": "PATIENT", "content": "It has been going on for 3 days and it is moderate pain"},
        headers=_auth(token),
    )

    process_res = await client.post(f"/api/consultations/{c_id}/process-intake", headers=_auth(token))
    assert process_res.status_code == 200
    history = process_res.json()["data"]["clinical_history"]
    assert history["severity"] == "moderate"
    assert history["duration"] is not None

    # Once severity/duration/chief_complaint are all known, the deterministic
    # follow-up path must consider intake for this complaint satisfied
    # instead of asking the same question again forever.
    assert process_res.json()["data"]["follow_up_questions"] == []
