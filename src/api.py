"""
api.py - DevProfile AI Backend

Endpoints:
  POST /auth/register       - create account
  POST /auth/login          - sign in, get JWT
  POST /auth/logout         - sign out
  GET  /auth/me             - get current user (protected)

  POST /analyze             - full analysis (protected, rate limited)
  GET  /history/{username}  - GitHub user analysis history
  GET  /my-searches         - current user's search history (protected)

  GET  /health              - health check
  GET  /status              - Ollama + DB status

Usage:
    uvicorn src.api:app --reload --port 8000
"""

import sys
import os
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator

from src.inference.pipeline import analyze
from src.llm.llm_engine     import check_ollama
from src.db import (
    is_configured, get_analysis_history,
    get_user, get_latest_analysis,
    register, login, logout,
    get_user_from_token, save_search, get_search_history,
)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DevProfile AI",
    version="2.0.0",
    description="ML-powered GitHub developer profile analyzer",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ── Rate limiter (in-memory, per IP) ─────────────────────────────────────────
# Max 10 analyze requests per minute per IP

_rate_store: dict = defaultdict(list)
RATE_LIMIT   = 10
RATE_WINDOW  = 60  # seconds


def _check_rate_limit(ip: str):
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
    if len(_rate_store[ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT} requests per minute."
        )
    _rate_store[ip].append(now)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency — extracts and verifies JWT. Raises 401 if invalid."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user


def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict | None:
    """Dependency — returns user if token present, None otherwise."""
    if not credentials:
        return None
    return get_user_from_token(credentials.credentials)


# ── Request / Response models ─────────────────────────────────────────────────

class AuthRequest(BaseModel):
    email:    EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v


class AnalyzeRequest(BaseModel):
    username: str
    use_llm:  bool = True

    @field_validator("username")
    @classmethod
    def username_clean(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty.")
        if len(v) > 39:
            raise ValueError("Invalid GitHub username.")
        return v


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/auth/register", status_code=201)
async def auth_register(req: AuthRequest):
    try:
        result = register(req.email, req.password)
        return {"message": "Account created successfully.", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/auth/login")
async def auth_login(req: AuthRequest):
    try:
        result = login(req.email, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/auth/logout")
async def auth_logout(current_user: dict = Depends(get_current_user),
                      credentials: HTTPAuthorizationCredentials = Depends(security)):
    logout(credentials.credentials)
    return {"message": "Logged out successfully."}


@app.get("/auth/me")
async def auth_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ── Analysis routes ───────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_user(
    req:     AnalyzeRequest,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
):
    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    result = analyze(req.username, use_cache=True, llm=req.use_llm)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Save to search history if user is logged in
    if current_user and is_configured():
        analysis_id = None
        try:
            gh_user = get_user(req.username)
            if gh_user:
                latest = get_latest_analysis(gh_user["id"])
                if latest:
                    analysis_id = latest["id"]
        except Exception:
            pass
        save_search(current_user["id"], req.username, analysis_id)

    return result


@app.get("/history/{username}")
async def github_history(username: str, limit: int = 10):
    if limit > 50:
        limit = 50
    rows = get_analysis_history(username, limit=limit)
    return {"username": username, "history": rows}


@app.get("/my-searches")
async def my_searches(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    history = get_search_history(current_user["id"], limit=min(limit, 50))
    return {"searches": history}


# ── System routes ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "DevProfile AI", "version": "2.0.0"}


@app.get("/status")
async def status():
    ollama = check_ollama()
    return {
        "api":      "ok",
        "ollama":   ollama,
        "database": is_configured(),
    }
