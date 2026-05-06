"""
auth.py - Supabase Authentication

Wraps Supabase Auth for:
  - register (email + password)
  - login
  - logout
  - token verification (get current user from JWT)
  - save / fetch search history per app user
"""

from .client import get_client, get_service_client


# ── Register ──────────────────────────────────────────────────────────────────

def register(email: str, password: str) -> dict:
    db = get_client()
    if not db:
        raise RuntimeError("Database not configured.")
    try:
        res = db.auth.sign_up({"email": email, "password": password})
        if res.user is None:
            raise ValueError("Registration failed. Email may already be in use.")
        return {
            "user":          _serialize_user(res.user),
            "access_token":  res.session.access_token  if res.session else None,
            "refresh_token": res.session.refresh_token if res.session else None,
        }
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(str(e))


# ── Login ─────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> dict:
    db = get_client()
    if not db:
        raise RuntimeError("Database not configured.")
    try:
        res = db.auth.sign_in_with_password({"email": email, "password": password})
        if res.user is None:
            raise ValueError("Invalid email or password.")
        return {
            "user":          _serialize_user(res.user),
            "access_token":  res.session.access_token,
            "refresh_token": res.session.refresh_token,
        }
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(str(e))


# ── Logout ────────────────────────────────────────────────────────────────────

def logout(access_token: str) -> bool:
    """
    Invalidate the token server-side.
    Uses the service client's admin API to sign out by JWT — this works
    regardless of which session the anon client currently holds.
    """
    svc = get_service_client()
    if not svc:
        return False
    try:
        svc.auth.admin.sign_out(access_token)
        return True
    except Exception:
        return False


# ── Verify token ──────────────────────────────────────────────────────────────

def get_user_from_token(access_token: str) -> dict | None:
    """
    Verify a JWT access token via Supabase and return the user dict.
    Returns None if token is invalid or expired.
    """
    db = get_client()
    if not db:
        return None
    try:
        res = db.auth.get_user(access_token)
        return _serialize_user(res.user) if res.user else None
    except Exception:
        return None


# ── Search history ────────────────────────────────────────────────────────────

def save_search(app_user_id: str, github_username: str, analysis_id: str | None) -> bool:
    db = get_service_client()
    if not db:
        return False
    try:
        db.table("search_history").insert({
            "app_user_id":     app_user_id,
            "github_username": github_username,
            "analysis_id":     analysis_id,
        }).execute()
        return True
    except Exception:
        return False


def get_search_history(app_user_id: str, limit: int = 20) -> list:
    db = get_service_client()
    if not db:
        return []
    try:
        res = (
            db.table("search_history")
            .select("github_username, searched_at, analysis_id")
            .eq("app_user_id", app_user_id)
            .order("searched_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_user(user) -> dict:
    return {
        "id":    str(user.id),
        "email": user.email,
    }
