import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# argon2-cffi's PasswordHasher defaults to the Argon2id variant.
_hasher = PasswordHasher()

SESSION_COOKIE_NAME = "session"
# Fixed product decision (docs/decisions.md §2), not per-environment config.
SESSION_TTL = timedelta(days=14)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_session_token() -> str:
    """An opaque, high-entropy session token (256 bits)."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """A fast, deterministic hash for lookup, not a password hash.

    The token already has 256 bits of entropy, so it doesn't need Argon2id's
    deliberate slowness; a session lookup happens on every authenticated
    request and must stay cheap.
    """
    return hashlib.sha256(token.encode()).hexdigest()
