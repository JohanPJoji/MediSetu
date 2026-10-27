"""
Authentication API routes.

Per ARCHITECTURE.md §51 (API DESIGN): mounted under /api/auth.
Per ARCHITECTURE.md §52 (API RESPONSE FORMAT): all success responses use
the {"success", "data", "message"} envelope (errors are handled centrally
in app.main's exception handlers, so routes just raise HTTPException).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.database.session import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.audit_service import record_audit_event
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        user = await register_user(
            db,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role=body.role,
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PATIENT_REGISTRATION_ONLY",
                "message": "Public registration is limited to patient accounts.",
            },
        )
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_REGISTERED",
                "message": "An account with this email already exists.",
            },
        )

    await record_audit_event(
        db, action="USER_REGISTERED", user_id=user.id,
        resource_type="User", resource_id=user.id, metadata={"role": user.role.value}
    )
    await db.commit()
    return {
        "success": True,
        "data": UserRead.model_validate(user).model_dump(mode="json"),
        "message": None,
    }


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        user = await authenticate_user(db, email=body.email, password=body.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Incorrect email or password.",
            },
        )

    token = create_access_token(subject=str(user.id), role=user.role.value)

    await record_audit_event(
        db, action="USER_LOGIN", user_id=user.id, resource_type="User", resource_id=user.id
    )
    await db.commit()
    return {
        "success": True,
        "data": Token(access_token=token).model_dump(),
        "message": None,
    }
