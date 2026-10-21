"""Small-team authorization API: Firebase ID token + private Google Sheets allowlist."""
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import auth
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.auth import default as google_auth_default
from googleapiclient.discovery import build

SHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_RANGE = os.environ.get("SHEET_RANGE", "Users!A2:E")
ALLOWED_ORIGINS = [x.strip() for x in os.environ.get("FRONTEND_ORIGINS", "").split(",") if x.strip()]
ROLES = {"admin", "editor", "viewer"}

firebase_admin.initialize_app()
app = FastAPI(title="Bioenergy Internal Team Authorization API")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
                   allow_methods=["GET"], allow_headers=["Authorization", "Content-Type"])

@lru_cache(maxsize=1)
def sheets_service():
    credentials, _ = google_auth_default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)

def verified_claims(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Firebase ID token")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Firebase ID token")
    try:
        return auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired ID token") from None

def require_member(claims: dict = Depends(verified_claims)):
    uid, email = claims.get("uid", ""), claims.get("email", "")
    if not uid or not email or not claims.get("email_verified", False):
        raise HTTPException(status_code=403, detail="Verified Google account required")
    if not SHEET_ID:
        raise HTTPException(status_code=503, detail="Allowlist is not configured")
    try:
        rows = (sheets_service().spreadsheets().values()
                .get(spreadsheetId=SHEET_ID, range=SHEET_RANGE)
                .execute().get("values", []))
    except Exception:
        raise HTTPException(status_code=503, detail="Cannot read private allowlist") from None

    for row in rows:
        allowed_uid, allowed_email, name, role, enabled = [str(v).strip() for v in (row + [""] * 5)[:5]]
        if allowed_uid != uid:
            continue
        if allowed_email and allowed_email.casefold() != email.casefold():
            break
        if enabled.upper() == "TRUE" and role in ROLES:
            return {"uid": uid, "email": email, "name": name, "role": role}
        break
    raise HTTPException(status_code=403, detail="Account is not authorized")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/me")
def me(user: dict = Depends(require_member)):
    return user

@app.get("/api/editor-only")
def editor(user: dict = Depends(require_member)):
    if user["role"] not in {"admin", "editor"}:
        raise HTTPException(status_code=403, detail="Editor role required")
    return {"ok": True}

@app.get("/api/admin-only")
def admin(user: dict = Depends(require_member)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return {"ok": True}
