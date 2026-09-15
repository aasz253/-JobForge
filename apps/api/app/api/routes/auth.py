"""Authentication: register, login, logout, password change."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.audit import record
from app.core.ratelimit import limiter
from app.core.security import (
    hash_password,
    hash_token,
    new_session_token,
    utcnow,
    verify_password,
)
from app.schemas.auth import ChangePasswordIn, LoginIn, RegisterIn, TokenOut, UserOut

from ...database import get_db
from ...models import Session as SessionModel
from ...models import User
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _rate_limit(ip: str) -> None:
    s = get_settings()
    if not limiter.hit(f"login:{ip}", s.rate_limit_login, s.rate_limit_login_window):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try again later.")


def _issue_token(db: Session, user: User, ip: str) -> TokenOut:
    token = new_session_token()
    s = get_settings()
    expires = utcnow() + timedelta(seconds=s.session_lifetime)
    db.add(
        SessionModel(
            user_id=user.id,
            token_hash=hash_token(token),
            created_at=utcnow(),
            expires_at=expires,
            ip=ip,
        )
    )
    db.commit()
    return TokenOut(access_token=token, token_type="bearer", expires_at=expires, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    _rate_limit(request.client.host if request.client else "unknown")
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record(db, user_id=user.id, action="auth.register", ip=request.client.host if request.client else "")
    return _issue_token(db, user, request.client.host if request.client else "")


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    ip = request.client.host if request.client else "unknown"
    _rate_limit(ip)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        record(db, user_id=user.id if user else None, action="auth.login_failed", ip=ip, outcome="FAIL")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")
    record(db, user_id=user.id, action="auth.login", ip=ip)
    return _issue_token(db, user, ip)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)) -> None:
    from fastapi.security.utils import get_authorization_scheme_param

    auth = request.headers.get("Authorization", "")
    scheme, token = get_authorization_scheme_param(auth)
    if scheme.lower() == "bearer" and token:
        sess = db.query(SessionModel).filter(SessionModel.token_hash == hash_token(token)).first()
        if sess:
            sess.revoked_at = utcnow()
            record(db, user_id=sess.user_id, action="auth.logout", ip=request.client.host if request.client else "")
            db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/change-password", response_model=UserOut)
def change_password(
    payload: ChangePasswordIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    if not verify_password(payload.current_password, user.password_hash):
        record(db, user_id=user.id, action="auth.change_password_failed", ip=request.client.host if request.client else "", outcome="FAIL")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    # rotate other sessions
    db.query(SessionModel).filter(SessionModel.user_id == user.id, SessionModel.revoked_at.is_(None)).update({"revoked_at": utcnow()})
    db.commit()
    record(db, user_id=user.id, action="auth.change_password", ip=request.client.host if request.client else "")
    return UserOut.model_validate(user)