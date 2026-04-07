"""
pipeline.py — Phase 1 Orchestrator

Single entry point for the entire data pipeline.

Usage:
    from src.pipeline.pipeline import run

    result = run("torvalds")
    print(result["features"])
    print(result["warnings"])
"""

from .collector import fetch_github_data
from .cleaner  import clean, validate
from .features import build_features


def run(username: str, use_cache: bool = True) -> dict:
    """
    Run the full Phase 1 pipeline for a GitHub username.

    Returns:
    {
        "username":  str,
        "features":  dict,      ← ML-ready feature vector
        "warnings":  list[str], ← data quality notes (non-fatal)
        "raw":       dict,      ← cleaned user + repos (for debugging)
    }

    Raises:
        ValueError  — invalid / not-found username
        RuntimeError — API / network failure
    """
    # Step 1 — Collect
    raw = fetch_github_data(username, use_cache=use_cache)

    # Step 2 — Clean & validate
    cleaned  = clean(raw)
    warnings = validate(cleaned)

    # Step 3 — Feature engineering
    features = build_features(cleaned)

    return {
        "username": cleaned["user"]["username"],
        "features": features,
        "warnings": warnings,
        "raw":      cleaned,
    }
