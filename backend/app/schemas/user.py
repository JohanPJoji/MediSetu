"""
Pydantic schemas for the User resource.

Per ARCHITECTURE.md §53 (VALIDATION): Pydantic request validation is the
second line of defense after frontend validation, before business/database
validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Request body for POST /api/auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole


class UserRead(BaseModel):
    """Public-safe representation of a User — never includes hashed_password."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminUserCreate(UserCreate):
    """Request body for administrator-created staff/admin accounts."""
    role: UserRole
