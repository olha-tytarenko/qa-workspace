from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApplicationError
from app.core.security import hash_password
from app.models.user import User

UNIQUE_EMAIL_CONSTRAINT = "uq_users_email"


class EmailAlreadyRegisteredError(ApplicationError):
    status_code = status.HTTP_409_CONFLICT
    code = "EMAIL_ALREADY_REGISTERED"

    def __init__(self, email: str) -> None:
        super().__init__("This email is already registered.", {"email": email})


def _is_email_uniqueness_violation(exc: IntegrityError) -> bool:
    # asyncpg's own UniqueViolationError (which carries `constraint_name`) is
    # wrapped by SQLAlchemy's DBAPI-compatibility exception, so it sits one
    # level deeper, at `exc.orig.__cause__`, not on `exc.orig` itself.
    error: BaseException | None = exc.orig
    while error is not None:
        if getattr(error, "constraint_name", None) == UNIQUE_EMAIL_CONSTRAINT:
            return True
        error = error.__cause__
    return False


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    """Create one user with a hashed password.

    `email` must already be normalized (trimmed, lowercased) by the caller's
    request schema. Owns its own transaction; on a duplicate-email race, the
    PostgreSQL unique constraint is the final authority, not a pre-check.
    """
    user = User(email=email, password_hash=hash_password(password))
    try:
        async with session.begin():
            session.add(user)
    except IntegrityError as exc:
        if _is_email_uniqueness_violation(exc):
            raise EmailAlreadyRegisteredError(email) from exc
        raise
    return user
