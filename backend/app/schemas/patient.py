"""
Pydantic schemas for the Patient resource.

Per ARCHITECTURE.md §53 (VALIDATION): Pydantic request validation is the
second line of defense after frontend validation, before business/database
validation. Per §13 (PATIENT MODEL): "Sensitive fields must be protected"
and "Avoid unnecessary duplication of patient data" — see the `age`
computed field note below.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.models.patient import PatientSex


def _compute_age(date_of_birth: date) -> int:
    """Derive age in whole years from date_of_birth (the single source of
    truth — see app/models/patient.py's note on why `age` is not a stored
    column)."""
    today = date.today()
    years = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


class PatientCreate(BaseModel):
    """Request body for POST /api/patients (create own profile)."""

    name: str = Field(min_length=1, max_length=255)
    date_of_birth: date
    sex: PatientSex
    contact_information: str = Field(min_length=1, max_length=255)
    preferred_language: str = Field(default="en", min_length=2, max_length=16)

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientUpdate(BaseModel):
    """Request body for PATCH /api/patients/me. All fields optional —
    only supplied fields are updated (partial update)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    sex: PatientSex | None = None
    contact_information: str | None = Field(default=None, min_length=1, max_length=255)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=16)

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_not_in_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value

    @model_validator(mode="after")
    def at_least_one_field_supplied(self) -> "PatientUpdate":
        if all(
            getattr(self, field) is None
            for field in ("name", "date_of_birth", "sex", "contact_information", "preferred_language")
        ):
            raise ValueError("At least one field must be supplied for update.")
        return self


class PatientRead(BaseModel):
    """
    Public-safe representation of a Patient.

    `age` is computed here from `date_of_birth` rather than read from a
    stored column — see app/models/patient.py's note on avoiding
    duplicated date_of_birth/age storage per ARCHITECTURE.md §13.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    date_of_birth: date
    sex: PatientSex
    contact_information: str
    preferred_language: str
    abha_id: str | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def age(self) -> int:
        return _compute_age(self.date_of_birth)
