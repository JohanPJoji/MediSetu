import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.voice import VoiceInputResponse, FollowUpResponse, SummaryResponse


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def test_voice_schemas_round_trip():
    voice = VoiceInputResponse(
        consultation_id="00000000-0000-0000-0000-000000000001",
        transcript="I have a headache",
        stt_confidence=0.91,
        assistant_message="How long have you had this problem?",
        follow_up_questions=["How long have you had this problem?"],
    )
    follow = FollowUpResponse(
        consultation_id=voice.consultation_id,
        question="How long have you had this problem?",
        follow_up_questions=["How long have you had this problem?"],
    )
    summary = SummaryResponse(
        consultation_id=voice.consultation_id,
        summary="Patient reports headache.",
        key_points=["Chief complaint: Headache"],
        clinical_history={"chief_complaint": "Headache"},
    )
    assert voice.transcript == "I have a headache"
    assert follow.question
    assert summary.key_points


@pytest.mark.asyncio
async def test_new_consultation_feature_routes_are_mounted(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/consultations/{consultation_id}/voice-input" in paths
    assert "/api/consultations/{consultation_id}/follow-up" in paths
    assert "/api/consultations/{consultation_id}/summary" in paths
    assert "/api/consultations/{consultation_id}/ai-suggestions" in paths
