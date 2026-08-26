"""Password hashing and session state.

Passwords are stored as salted PBKDF2-HMAC-SHA256 digests.  The previous
version of this app kept them in plain text in the SQLite file, which meant
anyone who could copy ``main.db`` had the owner's password.
"""

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 240_000
_SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    """Return an encoded digest: ``pbkdf2_sha256$iterations$salt$hash``."""
    if not password:
        raise ValueError("password must not be empty")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time check of ``password`` against a stored digest."""
    if not password or not encoded:
        return False
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != _ALGORITHM:
            return False
        expected = bytes.fromhex(digest_hex)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"),
            bytes.fromhex(salt_hex), int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def password_problem(password: str, confirm: str | None = None) -> str | None:
    """Human-readable reason the password is unacceptable, or ``None``."""
    if len(password) < 6:
        return "Password must be at least 6 characters."
    if confirm is not None and password != confirm:
        return "Passwords do not match."
    return None


@dataclass(frozen=True)
class Session:
    """The signed-in user for the lifetime of a window."""

    user_id: int
    username: str
    full_name: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def display_name(self) -> str:
        return self.full_name or self.username


def new_token() -> str:
    return secrets.token_urlsafe(24)


def machine_tag() -> str:
    """Short stable identifier for this install, used in backup filenames."""
    seed = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "shopdesk"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
