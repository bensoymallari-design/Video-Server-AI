"""Account bootstrap and lookup."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import SessionToken, User, utcnow
from app.security import hash_password, hash_token, new_session_token, verify_password

logger = logging.getLogger(__name__)

ROLES = {"admin", "operator", "viewer"}


def ensure_admin(db: Session, settings: Settings) -> None:
    existing = db.scalar(select(User).limit(1))
    if existing is not None:
        return
    password = settings.admin_password
    generated = False
    if not password:
        import secrets

        password = secrets.token_urlsafe(12)
        generated = True
    user = User(
        username=settings.admin_username,
        password_hash=hash_password(password),
        role="admin",
    )
    db.add(user)
    db.commit()
    if generated:
        path = settings.resolved_data_dir() / "initial-admin-password.txt"
        path.write_text(
            f"username={settings.admin_username}\npassword={password}\n",
            encoding="utf-8",
        )
        path.chmod(0o600)
        logger.warning(
            "No QUBIT_ADMIN_PASSWORD was set. The generated administrator password is in %s. "
            "Remove that file after storing the password elsewhere.",
            path,
        )
    else:
        logger.info("Created administrator account %s", settings.admin_username)


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User, ttl_hours: int) -> str:
    token = new_session_token()
    expires = utcnow() + timedelta(hours=ttl_hours)
    db.add(SessionToken(user_id=user.id, token_hash=hash_token(token), expires_at=expires))
    db.commit()
    return token


def user_for_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    row = db.scalar(select(SessionToken).where(SessionToken.token_hash == hash_token(token)))
    if row is None:
        return None
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        db.delete(row)
        db.commit()
        return None
    return db.get(User, row.user_id)


def delete_session(db: Session, token: str | None) -> None:
    if not token:
        return
    row = db.scalar(select(SessionToken).where(SessionToken.token_hash == hash_token(token)))
    if row is not None:
        db.delete(row)
        db.commit()


def set_password(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username, password_hash=hash_password(password), role="admin")
        db.add(user)
    else:
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return user
