"""Authenticated user administration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import AdminUserCreate, UserRead
from app.services.auth_service import EmailAlreadyRegisteredError, register_user_as_admin
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_current_user(user: User = Depends(get_current_user)) -> dict:
    return {
        "success": True,
        "data": UserRead.model_validate(user).model_dump(mode="json"),
        "message": None,
    }


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    return {
        "success": True,
        "data": [UserRead.model_validate(u).model_dump(mode="json") for u in users],
        "message": None,
    }


@router.post("")
async def create_user_as_admin(
    body: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    try:
        user = await register_user_as_admin(
            db,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role=body.role,
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
        db, action="USER_CREATED_BY_ADMIN", user_id=_admin.id,
        resource_type="User", resource_id=user.id, metadata={"role": user.role.value}
    )
    await db.commit()
    return {
        "success": True,
        "data": UserRead.model_validate(user).model_dump(mode="json"),
        "message": None,
    }
