"""
Authentication business logic.

Per ARCHITECTURE.md §9's repository structure, service-layer business
logic lives here, separate from the API route layer (app/api/auth.py) and
the ORM layer (app/models/user.py). Routes should stay thin and delegate
to this module.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole


class EmailAlreadyRegisteredError(Exception):
    """Raised when attempting to register an email that already exists."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials don't match any active user."""


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def register_user(
    db: AsyncSession, *, email: str, password: str, full_name: str, role: UserRole
) -> User:
    """
    Create a new User with a bcrypt-hashed password.

    Raises EmailAlreadyRegisteredError if the email is already taken.

    Public self-registration is intentionally restricted to PATIENT accounts.
    Staff/admin accounts must be created by an administrator or by the demo
    seed command. This prevents privilege escalation through public signup.
    """
    existing = await get_user_by_email(db, email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(email)

    if role is not UserRole.PATIENT:
        raise PermissionError("Public self-registration is limited to PATIENT accounts.")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
        role=UserRole.PATIENT,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, *, email: str, password: str) -> User:
    """
    Verify credentials and return the User.

    Raises InvalidCredentialsError if the email doesn't exist, the
    password doesn't match, or the account is inactive. Deliberately does
    not distinguish these cases in the exception/message, so a caller
    can't enumerate valid emails via error responses.
    """
    user = await get_user_by_email(db, email)
    if user is None or not user.is_active:
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()

    return user


async def register_user_as_admin(
    db: AsyncSession, *, email: str, password: str, full_name: str, role: UserRole
) -> User:
    """Create any role, but only when called from an authenticated admin endpoint."""
    existing = await get_user_by_email(db, email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(email)
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
