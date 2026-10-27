"""
Tests for Phase 2 — Authentication.

Per ARCHITECTURE.md §76 (TESTING STRATEGY): API tests must cover
authentication and authorization. This module exercises: registration,
duplicate-email rejection, login success/failure, an authenticated-only
route (/api/users/me), an admin-only route (/api/users) both allowed and
forbidden, and rejection of a missing/invalid/tampered token.

These tests hit a REAL PostgreSQL database (via the app's normal
app.database.session engine, driven by DATABASE_URL) — there is no mocking
of the database layer. Each test creates its own unique user (random
email) so tests can run in any order without colliding on the unique
email constraint, and there is no teardown/rollback: rows accumulate in
the `medisetu` database across test runs. See docs/CURRENT_STATE.md for
why this is an accepted, documented limitation for the prototype phase
rather than a production-grade isolated test database.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


def _unique_email(prefix: str) -> str:
    # NOTE: email-validator (used by Pydantic's EmailStr) treats .test as a
    # reserved/special-use TLD and rejects it, despite RFC 2606 reserving it
    # for exactly this purpose. Using .example.com's subdomain style instead
    # to stay valid while still obviously not a real mailbox.
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


async def _register(client: AsyncClient, *, email: str, password: str, role: str, full_name: str = "Test User"):
    return await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": full_name, "role": role},
    )


async def _login(client: AsyncClient, *, email: str, password: str):
    return await client.post("/api/auth/login", json={"email": email, "password": password})


async def _create_user_directly(*, email: str, password: str, role: UserRole, full_name: str = "Direct User"):
    async with AsyncSessionLocal() as db:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register_new_user_succeeds(client: AsyncClient) -> None:
    email = _unique_email("patient")
    response = await _register(client, email=email, password="correct-horse-1", role="PATIENT")

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == email
    assert body["data"]["role"] == "PATIENT"
    assert "hashed_password" not in body["data"]
    assert "password" not in body["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client: AsyncClient) -> None:
    email = _unique_email("dup")
    first = await _register(client, email=email, password="correct-horse-1", role="PATIENT")
    assert first.status_code == 201

    second = await _register(client, email=email, password="another-password-2", role="PATIENT")
    assert second.status_code == 409
    body = second.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.asyncio
async def test_login_with_correct_credentials_returns_token(client: AsyncClient) -> None:
    email = _unique_email("login")
    password = "correct-horse-3"
    await _create_user_directly(email=email, password=password, role=UserRole.DOCTOR)

    response = await _login(client, email=email, password=password)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token_type"] == "bearer"
    assert isinstance(body["data"]["access_token"], str) and len(body["data"]["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_with_wrong_password_rejected(client: AsyncClient) -> None:
    email = _unique_email("wrongpw")
    await _register(client, email=email, password="correct-horse-4", role="PATIENT")

    response = await _login(client, email=email, password="totally-wrong-password")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_with_unknown_email_rejected(client: AsyncClient) -> None:
    response = await _login(client, email=_unique_email("nobody"), password="whatever-1")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


@pytest.mark.asyncio
async def test_me_returns_own_profile_with_valid_token(client: AsyncClient) -> None:
    email = _unique_email("me")
    password = "correct-horse-5"
    await _create_user_directly(email=email, password=password, role=UserRole.NURSE, full_name="Nina Nurse")
    login_response = await _login(client, email=email, password=password)
    token = login_response.json()["data"]["access_token"]

    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["email"] == email
    assert body["data"]["role"] == "NURSE"
    assert body["data"]["full_name"] == "Nina Nurse"


@pytest.mark.asyncio
async def test_list_users_forbidden_for_non_admin(client: AsyncClient) -> None:
    email = _unique_email("nonadmin")
    password = "correct-horse-6"
    await _register(client, email=email, password=password, role="PATIENT")
    login_response = await _login(client, email=email, password=password)
    token = login_response.json()["data"]["access_token"]

    response = await client.get("/api/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_list_users_allowed_for_admin(client: AsyncClient) -> None:
    email = _unique_email("admin")
    password = "correct-horse-7"
    await _create_user_directly(email=email, password=password, role=UserRole.ADMIN)
    login_response = await _login(client, email=email, password=password)
    token = login_response.json()["data"]["access_token"]

    response = await client.get("/api/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # The admin we just created must appear in the list.
    assert any(u["email"] == email for u in body["data"])


@pytest.mark.asyncio
async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await _register(
        client, email=_unique_email("shortpw"), password="short", role="PATIENT"
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_public_registration_rejects_privileged_role(client: AsyncClient) -> None:
    response = await _register(
        client,
        email=_unique_email("privileged"),
        password="correct-horse-9",
        role="ADMIN",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PATIENT_REGISTRATION_ONLY"


@pytest.mark.asyncio
async def test_register_rejects_invalid_role(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={
            "email": _unique_email("badrole"),
            "password": "correct-horse-8",
            "full_name": "Bad Role",
            "role": "SUPERUSER",
        },
    )
    assert response.status_code == 422
