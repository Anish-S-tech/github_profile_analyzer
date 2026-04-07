"""
cleaner.py — Data Cleaning & Validation Layer

Takes raw output from collector.py and returns safe, typed, validated data.
Never crashes. Always returns usable output.

Guarantees:
- All numeric fields are int/float (never None)
- All string fields are str (never None)
- Dates are validated ISO strings or empty string
- Repos with missing critical fields are kept with safe defaults
- Language None is preserved (handled downstream in features.py)
"""

from datetime import datetime, timezone


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _safe_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _safe_date(value) -> str:
    """Validate ISO date string. Returns empty string if invalid."""
    if not value:
        return ""
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    except (ValueError, AttributeError):
        return ""


def _safe_list(value) -> list:
    if isinstance(value, list):
        return value
    return []


# ── Public API ────────────────────────────────────────────────────────────────

def clean(raw: dict) -> dict:
    """
    Input:  raw dict from collector.fetch_github_data()
    Output: cleaned dict with same shape but guaranteed safe types
    """
    raw_user  = raw.get("user", {}) or {}
    raw_repos = raw.get("repos", []) or []

    user = {
        "username":   _safe_str(raw_user.get("username"), "unknown"),
        "followers":  _safe_int(raw_user.get("followers")),
        "following":  _safe_int(raw_user.get("following")),
        "created_at": _safe_date(raw_user.get("created_at")),
        "bio":        _safe_str(raw_user.get("bio")),
        "location":   _safe_str(raw_user.get("location")),
    }

    repos = []
    for r in raw_repos:
        if not isinstance(r, dict):
            continue
        repos.append({
            "name":       _safe_str(r.get("name")),
            "stars":      _safe_int(r.get("stars")),
            "forks":      _safe_int(r.get("forks")),
            "language":   r.get("language"),   # keep None — features.py handles it
            "created_at": _safe_date(r.get("created_at")),
            "updated_at": _safe_date(r.get("updated_at")),
            "topics":     _safe_list(r.get("topics")),
        })

    return {"user": user, "repos": repos}


def validate(cleaned: dict) -> list[str]:
    """
    Returns a list of warning strings for any data quality issues.
    Empty list means data is clean.
    """
    warnings = []
    user = cleaned.get("user", {})
    repos = cleaned.get("repos", [])

    if not user.get("created_at"):
        warnings.append("Missing account creation date — age-based features will be 0.")
    if not repos:
        warnings.append("No repositories found — repo-based features will be 0.")
    if user.get("followers", 0) == 0:
        warnings.append("Zero followers — growth_rate and ff_ratio will be minimal.")

    return warnings
