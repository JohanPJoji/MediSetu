"""Create deterministic local demo accounts.

Usage from backend/:
    python -m app.seed_demo
"""

import asyncio
from datetime import date

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient, PatientSex


DEMO_USERS = [
    ("admin@medisetu.dev", "Admin@123456", "MediSetu Admin", UserRole.ADMIN),
    ("doctor@medisetu.dev", "Doctor@12345", "Demo Doctor", UserRole.DOCTOR),
    ("pharmacy@medisetu.dev", "Pharmacy@12345", "Demo Pharmacy", UserRole.PHARMACY),
    ("nurse@medisetu.dev", "Nurse@12345", "Demo Nurse", UserRole.NURSE),
    ("patient@medisetu.dev", "Patient@12345", "Demo Patient", UserRole.PATIENT),
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        for email, password, name, role in DEMO_USERS:
            existing = await db.scalar(select(User).where(User.email == email))
            if existing:
                continue
            db.add(
                User(
                    email=email,
                    hashed_password=hash_password(password),
                    full_name=name,
                    role=role,
                    is_active=True,
                )
            )
        await db.commit()

        patient_user = await db.scalar(select(User).where(User.email == "patient@medisetu.dev"))
        if patient_user:
            existing_patient = await db.scalar(select(Patient).where(Patient.user_id == patient_user.id))
            if existing_patient is None:
                db.add(
                    Patient(
                        user_id=patient_user.id,
                        name="Demo Patient",
                        date_of_birth=date(2000, 1, 1),
                        sex=PatientSex.MALE,
                        contact_information="demo@medisetu.dev",
                        preferred_language="en",
                    )
                )

        doctor_user = await db.scalar(select(User).where(User.email == "doctor@medisetu.dev"))
        if doctor_user:
            existing_doctor = await db.scalar(select(Doctor).where(Doctor.user_id == doctor_user.id))
            if existing_doctor is None:
                existing_registration = await db.scalar(
                    select(Doctor).where(Doctor.registration_number == "DEMO-DR-001")
                )
                if existing_registration is None:
                    db.add(
                        Doctor(
                            user_id=doctor_user.id,
                            name="Demo Doctor",
                            department="General Medicine",
                            specialization="Internal Medicine",
                            registration_number="DEMO-DR-001",
                            is_available=True,
                        )
                    )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
