"""Password hashing, session tokens, and a small login throttle.

The AI surface does not exist in this phase. Nothing in this module executes
a shell command.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

PBKDF2_ROUNDS = 200_000
MIN_PASSWORD_LENGTH = 8
LOGIN_WINDOW_SECONDS = 60
LOGIN_MAX_FAILURES = 8

login_attempts: dict[str, deque[float]] = defaultdict(deque)


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds_text, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds_text),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def login_blocked(key: str) -> bool:
    now = time.monotonic()
    bucket = login_attempts[key]
    while bucket and now - bucket[0] > LOGIN_WINDOW_SECONDS:
        bucket.popleft()
    return len(bucket) >= LOGIN_MAX_FAILURES


def record_login_failure(key: str) -> None:
    login_attempts[key].append(time.monotonic())


def clear_login_failures(key: str) -> None:
    login_attempts.pop(key, None)
