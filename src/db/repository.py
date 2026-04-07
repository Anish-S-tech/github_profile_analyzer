"""
repository.py — Database Repository

All read/write operations for the 3 tables.
Every function is safe — returns None/False on failure
so the app works even if DB is unavailable.

Tables:
    users     — GitHub profile data
    analysis  — ML + LLM results (history kept)
    languages — language distribution per user
"""

from datetime import datetime, timezone, timedelta
from .client import get_client

CACHE_TTL_HOURS = 24


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_fresh(timestamp_str: str) -> bool:
    """Return True if timestamp is within CACHE_TTL_HOURS."""
    if not timestamp_str:
        return False
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (_now() - ts) < timedelta(hours=CACHE_TTL_HOURS)
    except (ValueError, TypeError):
        return False


# ── Users ─────────────────────────────────────────────────────────────────────

def get_user(username: str) -> dict | None:
    """Fetch user row by username. Returns None if not found."""
    db = get_client()
    if not db:
        return None
    try:
        res = db.table("users").select("*").eq("username", username).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def upsert_user(username: str, profile: dict) -> dict | None:
    """
    Insert or update user row from Phase 1 profile dict.
    Returns the saved row or None on failure.
    """
    db = get_client()
    if not db:
        return None
    try:
        row = {
            "username":           username,
            "followers":          profile.get("followers",        0),
            "following":          profile.get("following",        0),
            "repo_count":         profile.get("repo_count",       0),
            "total_stars":        profile.get("total_stars",      0),
            "total_forks":        profile.get("total_forks",      0),
            "top_language":       profile.get("top_language"),
            "account_created_at": None,
            "last_fetched_at":    _now().isoformat(),
        }
        res = (
            db.table("users")
            .upsert(row, on_conflict="username")
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception:
        return None


# ── Analysis ──────────────────────────────────────────────────────────────────

def get_latest_analysis(user_id: str) -> dict | None:
    """
    Fetch the most recent analysis row for a user.
    Returns None if not found.
    """
    db = get_client()
    if not db:
        return None
    try:
        res = (
            db.table("analysis")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception:
        return None


def is_analysis_fresh(user_id: str) -> bool:
    """Return True if a fresh analysis (within 24h) exists for this user."""
    row = get_latest_analysis(user_id)
    if not row:
        return False
    return _is_fresh(row.get("created_at", ""))


def save_analysis(user_id: str, metrics: dict, insights: dict | None) -> dict | None:
    """
    Insert a new analysis row. Always inserts (never updates) to keep history.
    Returns the saved row or None on failure.
    """
    db = get_client()
    if not db:
        return None
    try:
        row = {
            "user_id":            user_id,
            "impact_score":       metrics.get("impact_score",       0),
            "impact_level":       metrics.get("impact_level",       "Explorer"),
            "impact_probability": metrics.get("impact_probability", 0),
            "skill_type":         metrics.get("skill_type"),
            "contribution_type":  metrics.get("contribution_type"),
            "maturity_score":     metrics.get("maturity_score",     0),
            "maturity_level":     metrics.get("maturity_level",     "Early Stage"),
            "created_at":         _now().isoformat(),
        }

        if insights:
            row["llm_summary"]     = insights.get("summary",     "")
            row["llm_strengths"]   = insights.get("strengths",   [])
            row["llm_weaknesses"]  = insights.get("weaknesses",  [])
            row["llm_suggestions"] = insights.get("suggestions", [])
            row["llm_growth_plan"] = insights.get("growth_plan", "")

        res = db.table("analysis").insert(row).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def get_analysis_history(username: str, limit: int = 10) -> list:
    """
    Return the last N analysis rows for a user (for history/growth tracking).
    Returns empty list on failure.
    """
    db = get_client()
    if not db:
        return []
    try:
        user = get_user(username)
        if not user:
            return []
        res = (
            db.table("analysis")
            .select("impact_score, maturity_score, impact_level, created_at")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


# ── Languages ─────────────────────────────────────────────────────────────────

def save_languages(user_id: str, languages: dict) -> bool:
    """
    Replace language rows for a user with the latest distribution.
    Deletes old rows first, then inserts fresh ones.
    Returns True on success.
    """
    db = get_client()
    if not db or not languages:
        return False
    try:
        # Delete old language rows for this user
        db.table("languages").delete().eq("user_id", user_id).execute()

        # Insert new rows
        rows = [
            {
                "user_id":    user_id,
                "language":   lang,
                "percentage": round(pct * 100, 2),
                "created_at": _now().isoformat(),
            }
            for lang, pct in languages.items()
        ]
        db.table("languages").insert(rows).execute()
        return True
    except Exception:
        return False


def get_languages(user_id: str) -> dict:
    """
    Fetch language distribution for a user.
    Returns { language: percentage } dict.
    """
    db = get_client()
    if not db:
        return {}
    try:
        res = (
            db.table("languages")
            .select("language, percentage")
            .eq("user_id", user_id)
            .order("percentage", desc=True)
            .execute()
        )
        return {r["language"]: r["percentage"] for r in (res.data or [])}
    except Exception:
        return {}
