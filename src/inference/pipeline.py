"""
pipeline.py — Inference Pipeline Controller

Full flow:
    username
        -> [DB] Check cache (fresh analysis within 24h?)
            -> YES: return cached result immediately
            -> NO:
                -> Phase 1 (fetch + clean + features)
                -> Phase 2 (ML models)
                -> Post-processing
                -> LLM Layer
                -> [DB] Store user + analysis + languages
                -> Return result

Usage:
    from src.inference.pipeline import analyze
    result = analyze("torvalds")

On error returns: { "error": "reason" }
"""

from src.pipeline.pipeline        import run as phase1_run
from src.inference.predictor      import run_all
from src.inference.postprocessing import build_output
from src.llm.llm_layer            import generate_insights
from src.db import (
    is_configured,
    get_user, upsert_user,
    get_latest_analysis, is_analysis_fresh,
    save_analysis, save_languages,
)


def _build_result_from_cache(user_row: dict, analysis_row: dict) -> dict:
    """Reconstruct the standard result dict from cached DB rows."""
    insights = None
    if analysis_row.get("llm_summary"):
        insights = {
            "summary":     analysis_row.get("llm_summary",     ""),
            "strengths":   analysis_row.get("llm_strengths",   []),
            "weaknesses":  analysis_row.get("llm_weaknesses",  []),
            "suggestions": analysis_row.get("llm_suggestions", []),
            "growth_plan": analysis_row.get("llm_growth_plan", ""),
        }

    return {
        "username": user_row["username"],
        "profile": {
            "followers":        user_row.get("followers",    0),
            "following":        user_row.get("following",    0),
            "repo_count":       user_row.get("repo_count",   0),
            "total_stars":      user_row.get("total_stars",  0),
            "total_forks":      user_row.get("total_forks",  0),
            "top_language":     user_row.get("top_language", "General Developer"),
            "account_age_days": 0,
        },
        "metrics": {
            "impact_score":       analysis_row.get("impact_score",       0),
            "impact_level":       analysis_row.get("impact_level",       "Explorer"),
            "impact_probability": analysis_row.get("impact_probability", 0),
            "skill_type":         analysis_row.get("skill_type",         "Multi-stack Developer"),
            "contribution_type":  analysis_row.get("contribution_type",  "Unknown"),
            "maturity_score":     analysis_row.get("maturity_score",     0),
            "maturity_level":     analysis_row.get("maturity_level",     "Early Stage"),
        },
        "languages":  {},
        "warnings":   ["Served from cache."],
        "insights":   insights,
        "cached":     True,
    }


def analyze(username: str, use_cache: bool = True, llm: bool = True) -> dict:
    """
    Full inference pipeline: username -> structured insights.
    Returns result dict on success, { "error": str } on failure.
    """
    username = username.strip()

    # ── Step 1: Check DB cache ─────────────────────────────────────────────────
    if use_cache and is_configured():
        user_row = get_user(username)
        if user_row and is_analysis_fresh(user_row["id"]):
            analysis_row = get_latest_analysis(user_row["id"])
            if analysis_row:
                return _build_result_from_cache(user_row, analysis_row)

    # ── Step 2: Phase 1 — fetch, clean, build features ────────────────────────
    try:
        phase1 = phase1_run(username, use_cache=use_cache)
    except ValueError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": f"API error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error during data fetch: {e}"}

    features = phase1["features"]
    warnings = phase1["warnings"]
    uname    = phase1["username"]

    # ── Step 3: Phase 2 — run all 4 models ────────────────────────────────────
    try:
        predictions = run_all(features)
    except FileNotFoundError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Model inference failed: {e}"}

    # ── Step 4: Post-process → structured output ───────────────────────────────
    result = build_output(uname, features, predictions, warnings)

    # ── Step 5: LLM Layer ─────────────────────────────────────────────────────
    if llm:
        result["insights"] = generate_insights(result)
    else:
        result["insights"] = None

    result["cached"] = False

    # ── Step 6: Persist to DB (non-blocking — never fails the request) ─────────
    if is_configured():
        try:
            user_row = upsert_user(uname, result["profile"])
            if user_row:
                save_analysis(user_row["id"], result["metrics"], result["insights"])
                save_languages(user_row["id"], result["languages"])
        except Exception:
            pass  # DB errors never break the response

    return result
