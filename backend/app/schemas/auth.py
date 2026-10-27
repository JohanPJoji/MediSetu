"""Pydantic schemas for authentication requests/responses."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request body for POST /api/auth/login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Response body for a successful login."""

    access_token: str
    token_type: str = "bearer"
