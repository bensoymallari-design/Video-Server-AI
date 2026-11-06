"""Local username and password sessions."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import COOKIE_NAME, get_db, require_user
from app.models import User
from app.schemas import LoginRequest, UserOut
from app.security import clear_login_failures, login_blocked, record_login_failure
from app.services.accounts import authenticate, create_session, delete_session
from app.services.audit import record

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> UserOut:
    address = request.client.host if request.client else "unknown"
    throttle_key = f"{address}:{body.username}"
    if login_blocked(throttle_key):
        record(db, body.username, "auth.login", False, {"reason": "rate_limited"})
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many sign-in attempts")
    user = authenticate(db, body.username, body.password)
    if user is None:
        record_login_failure(throttle_key)
        record(db, body.username, "auth.login", False, {"reason": "rejected"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    clear_login_failures(throttle_key)
    token = create_session(db, user, get_settings().token_ttl_hours)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=get_settings().token_ttl_hours * 3600,
        path="/",
    )
    record(db, user.username, "auth.login", True, {})
    return UserOut(username=user.username, role=user.role)


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    qubit_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> dict[str, str]:
    delete_session(db, qubit_session)
    response.delete_cookie(COOKIE_NAME, path="/")
    record(db, user.username, "auth.logout", True, {})
    return {"status": "signed_out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(require_user)) -> UserOut:
    return UserOut(username=user.username, role=user.role)
