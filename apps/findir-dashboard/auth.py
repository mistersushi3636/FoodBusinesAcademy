"""
Auth для PNP MR.SUSHI: cookie-сессии + bcrypt + роли (owner/manager).
"""
from __future__ import annotations

import os
from typing import Optional

import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request
from fastapi.responses import RedirectResponse

SECRET_KEY = os.getenv("DASHBOARD_SECRET", "mrsushi-findir-dev-secret-CHANGE-ME")
COOKIE_NAME = "mrsushi_findir"
SESSION_TTL = 60 * 60 * 24 * 7  # 7 дней

_s = URLSafeTimedSerializer(SECRET_KEY)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode()[:72], hashed.encode())


def make_cookie(user_id: int, role: str) -> str:
    return _s.dumps({"uid": user_id, "role": role})


def read_cookie(token: str) -> Optional[dict]:
    try:
        return _s.loads(token, max_age=SESSION_TTL)
    except (BadSignature, SignatureExpired):
        return None


def get_session(request: Request) -> Optional[dict]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return read_cookie(token)


def redirect_login() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=302)


def is_owner(session: Optional[dict]) -> bool:
    return bool(session and session.get("role") == "owner")
