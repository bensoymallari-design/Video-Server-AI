"""Request dependencies."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import session_scope
from app.models import User
from app.services.accounts import user_for_token

COOKIE_NAME = "qubit_session"


def get_db() -> Generator[Session, None, None]:
    with session_scope() as db:
        yield db


def optional_user(
    db: Session = Depends(get_db),
    qubit_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User | None:
    return user_for_token(db, qubit_session)


def require_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(require_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account cannot perform that action")
        return user

    return dependency
