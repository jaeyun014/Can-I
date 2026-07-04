from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from fastapi import Header, HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings
from app.models.schemas import AuthSession, AuthUser


logger = logging.getLogger(__name__)


@dataclass
class SessionRecord:
    token: str
    user: AuthUser


_sessions: dict[str, SessionRecord] = {}


def verify_google_credential(credential: str) -> AuthSession:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured. Set GOOGLE_CLIENT_ID.",
        )

    try:
        payload = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            settings.google_client_id,
            clock_skew_in_seconds=30,
        )
    except Exception as exc:
        logger.warning("Google credential verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google credential verification failed.",
        ) from exc

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is missing.",
        )

    user = AuthUser(
        email=email,
        name=payload.get("name", ""),
        picture=payload.get("picture", ""),
    )
    token = uuid4().hex
    _sessions[token] = SessionRecord(token=token, user=user)
    return AuthSession(token=token, user=user)


def get_user_from_token(token: Optional[str]) -> Optional[AuthUser]:
    if not token:
        return None
    record = _sessions.get(token)
    return record.user if record else None


def get_optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[AuthUser]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return get_user_from_token(token)


def get_required_user(authorization: Optional[str] = Header(default=None)) -> AuthUser:
    user = get_optional_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login is required.",
        )
    return user


def delete_session(token: str) -> None:
    _sessions.pop(token, None)
