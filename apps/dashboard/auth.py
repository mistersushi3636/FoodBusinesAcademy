from __future__ import annotations

import os
from typing import Optional

import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request
from fastapi.responses import RedirectResponse

SECRET_KEY = os.getenv("DASHBOARD_SECRET", "fba-dashboard-secret-2026-mistersushi")
COOKIE_NAME = "fba_session"
SESSION_TTL = 60 * 60 * 24 * 7  # 7 дней

_s = URLSafeTimedSerializer(SECRET_KEY)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode()[:72], hashed.encode())


def make_cookie(project_slug: str) -> str:
    return _s.dumps({"slug": project_slug})


def read_cookie(token: str) -> Optional[str]:
    try:
        data = _s.loads(token, max_age=SESSION_TTL)
        return data.get("slug")
    except (BadSignature, SignatureExpired):
        return None


def get_session_slug(request: Request) -> Optional[str]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return read_cookie(token)


def redirect_to_login(slug: str) -> RedirectResponse:
    return RedirectResponse(url=f"/p/{slug}/login", status_code=302)
