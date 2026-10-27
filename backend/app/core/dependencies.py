"""
Authentication/authorization FastAPI dependencies.

Per ARCHITECTURE.md §11 ("protected routes", "role-based authorization")
and §12 (ROLE-BASED ACCESS CONTROL): every non-public route should depend
on `get_current_user` (authentication) and, where a route is role-specific,
`require_role(...)` (authorization). Frontend-only restriction is
explicitly called out as insufficient (§10) — enforcement must happen here,
in the backend.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_id

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the authenticated User from the `Authorization: Bearer <token>`
    header. Raises 401 for any missing/invalid/expired token, or for a
    well-formed token whose user no longer exists or was deactivated.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "NOT_AUTHENTICATED", "message": "Authentication required."},
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_role(*allowed_roles: UserRole | list[UserRole] | tuple[UserRole, ...] | set[UserRole]):
    """
    Dependency factory for RBAC.

    Supports both historical calling styles used by this repository:
      require_role(UserRole.ADMIN)
      require_role(UserRole.DOCTOR, UserRole.NURSE)
      require_role([UserRole.DOCTOR, UserRole.NURSE])

    The normalized role tuple is captured once when the dependency is built.
    """
    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple, set)):
        normalized_roles = tuple(allowed_roles[0])
    else:
        normalized_roles = tuple(allowed_roles)

    if not normalized_roles or any(not isinstance(role, UserRole) for role in normalized_roles):
        raise ValueError("require_role() requires one or more valid UserRole values")

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "You do not have permission to perform this action.",
                },
            )
        return user

    return _check
