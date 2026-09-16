"""Security primitives: password hashing, session tokens, field encryption.

- Passwords: PBKDF2-HMAC-SHA256, per-user random salt, constant-time compare
  (stdlib only — no third-party bcrypt compatibility churn).
- Sessions: `secrets.token_urlsafe` tokens; only the SHA-256 *hash* of the
  token is persisted, so a DB leak cannot replay sessions.
- Field encryption: Fernet (AES) for sensitive values at rest, key from env.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return "pbkdf2_sha256$260000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(dk, expected)
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    # PostgreSQL (timestamptz) returns timezone-aware datetimes; produce aware
    # UTC so comparisons are always consistent. SQLite returns naive datetimes
    # regardless of a column's timezone=True flag, so callers must normalize
    # stored values to aware before comparing (see api/deps.py).
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Field-level encryption (sensitive values at rest)
# ---------------------------------------------------------------------------


def _fernet() -> Fernet | None:
    key = __import__("app.config", fromlist=["get_settings"]).get_settings().field_encryption_key
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError):
        return None


def encrypt_value(value: str) -> str:
    f = _fernet()
    if f is None:
        return value  # no key configured: store plainly (dev mode)
    token = f.encrypt(value.encode("utf-8"))
    return "enc:" + token.decode()


def decrypt_value(value: str | None) -> str:
    if not value:
        return ""
    if not value.startswith("enc:"):
        return value
    f = _fernet()
    if f is None:
        return ""
    try:
        return f.decrypt(value[4:].encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""

def mask_value(value: str) -> str:
    """Mask a secret for logs/audit trails."""
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:2]}****{value[-2:]}"


def generate_secret(nbytes: int = 32) -> str:
    return secrets.token_hex(nbytes)