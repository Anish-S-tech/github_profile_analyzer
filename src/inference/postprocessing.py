"""
postprocessing.py — Post-Processing Layer

Converts raw model outputs + Phase 1 features into the final
structured output with fair, human-readable scores.

Score design:
  Impact  : base_score + weighted log-scaled contributions → clamped 0-100
  Maturity: log-scaled composite → remapped to 20-100 range for active users

Level mappings:
  Impact  : 0-20 Explorer | 20-40 Growing | 40-70 Advanced | 70-100 High Impact
  Maturity: 0-25 Early Stage | 25-50 Developing | 50-75 Experienced | 75-100 Expert
"""

import math

# ── Level mappings ────────────────────────────────────────────────────────────

_IMPACT_LEVELS = [
    (70, 101, "High Impact"),
    (40,  70, "Advanced"),
    (20,  40, "Growing"),
    (0,   20, "Explorer"),
]

_MATURITY_LEVELS = [
    (75, 101, "Expert"),
    (50,  75, "Experienced"),
    (25,  50, "Developing"),
    (0,   25, "Early Stage"),
]


def _score_to_level(score: float, mapping: list) -> str:
    for lo, hi, label in mapping:
        if lo <= score < hi:
            return label
    return mapping[-1][2]


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lo=0.0, hi=100.0) -> float:
    return round(max(lo, min(hi, value)), 2)


# ── Impact score formula ──────────────────────────────────────────────────────
#
# Combines:
#   1. Base score  — 10 pts if user has any repos (dead profiles stay 0)
#   2. ML signal   — model probability reshaped via sqrt to spread mid-range
#   3. Log-scaled feature contributions — followers, stars, repos, growth
#   4. All components normalized and weighted, then clamped to 100
#
# Reference ceilings used for normalization (99th-percentile real values):
#   followers  : 300 000
#   total_stars: 500 000
#   repo_count : 500
#   growth_rate: 100  (followers/day)

_CEIL_FOLLOWERS   = 300_000
_CEIL_STARS       = 500_000
_CEIL_REPOS       = 500
_CEIL_GROWTH      = 100.0


def _norm_log(value: float, ceiling: float) -> float:
    """Log-normalize a value against a ceiling → 0..1"""
    if value <= 0 or ceiling <= 0:
        return 0.0
    return min(math.log1p(value) / math.log1p(ceiling), 1.0)


def _compute_impact_score(features: dict, raw_prob: float) -> float:
    repo_count  = _safe_float(features.get("repo_count",  0))
    followers   = _safe_float(features.get("followers",   0))
    total_stars = _safe_float(features.get("total_stars", 0))
    growth_rate = _safe_float(features.get("growth_rate", 0))

    # 1. Base score — only if user has repos
    base = 10.0 if repo_count > 0 else 0.0

    # 2. ML model signal (sqrt reshapes 0.0 → 0.0, 0.5 → 0.71, 1.0 → 1.0)
    #    Weighted at 25 pts max
    ml_component = math.sqrt(max(raw_prob, 0.0)) * 25.0

    # 3. Log-scaled feature contributions
    follower_component = _norm_log(followers,   _CEIL_FOLLOWERS) * 25.0
    stars_component    = _norm_log(total_stars, _CEIL_STARS)     * 25.0
    repos_component    = _norm_log(repo_count,  _CEIL_REPOS)     * 10.0
    growth_component   = _norm_log(growth_rate, _CEIL_GROWTH)    * 5.0

    score = base + ml_component + follower_component + stars_component + repos_component + growth_component
    return _clamp(score)


# ── Maturity score formula ────────────────────────────────────────────────────
#
# Raw model output is MinMax-scaled 0-100 against the training set,
# which means a beginner always gets ~0 relative to top devs.
#
# We remap it:
#   - Dead profile (0 repos, 0 stars) → stays near 0
#   - Any active user → minimum 20, scales up to 100
#   - Uses log-scaled stars + repos + age as a composite

_CEIL_AGE = 6000  # ~16 years


def _compute_maturity_score(features: dict, raw_score: float) -> float:
    repo_count        = _safe_float(features.get("repo_count",        0))
    total_stars       = _safe_float(features.get("total_stars",       0))
    account_age_days  = _safe_float(features.get("account_age_days",  1))
    topic_diversity   = _safe_float(features.get("topic_diversity",   0))

    # Dead profile
    if repo_count == 0 and total_stars == 0:
        return _clamp(raw_score * 0.2)

    # Log-scaled composite
    age_component      = _norm_log(account_age_days, _CEIL_AGE)   * 30.0
    stars_component    = _norm_log(total_stars,       _CEIL_STARS) * 35.0
    repos_component    = _norm_log(repo_count,        _CEIL_REPOS) * 20.0
    topic_component    = _norm_log(topic_diversity,   50)          * 5.0

    # Blend: 60% composite + 40% model signal, then remap to 20-100
    composite = age_component + stars_component + repos_component + topic_component
    blended   = 0.6 * composite + 0.4 * raw_score

    # Remap: active users get minimum 20
    remapped = 20.0 + (blended / 100.0) * 80.0
    return _clamp(remapped)


# ── Public API ────────────────────────────────────────────────────────────────

def build_output(
    username:    str,
    features:    dict,
    predictions: dict,
    warnings:    list,
) -> dict:
    raw_prob        = _safe_float(predictions.get("impact_probability", 0))
    raw_maturity    = _safe_float(predictions.get("maturity_score",     0))

    impact_score    = _compute_impact_score(features, raw_prob)
    maturity_score  = _compute_maturity_score(features, raw_maturity)

    return {
        "username": username,

        "profile": {
            "followers":        int(_safe_float(features.get("followers",        0))),
            "following":        int(_safe_float(features.get("following",        0))),
            "repo_count":       int(_safe_float(features.get("repo_count",       0))),
            "total_stars":      int(_safe_float(features.get("total_stars",      0))),
            "total_forks":      int(_safe_float(features.get("total_forks",      0))),
            "top_language":     predictions.get("top_language", "General Developer"),
            "account_age_days": int(_safe_float(features.get("account_age_days", 0))),
        },

        "metrics": {
            "impact_score":       impact_score,
            "impact_probability": _clamp(raw_prob, 0.0, 1.0),
            "impact_level":       _score_to_level(impact_score,  _IMPACT_LEVELS),
            "skill_type":         predictions.get("skill_type",        "Unknown"),
            "contribution_type":  predictions.get("contribution_type", "Unknown"),
            "maturity_score":     maturity_score,
            "maturity_level":     _score_to_level(maturity_score, _MATURITY_LEVELS),
        },

        "languages": features.get("languages", {}),
        "warnings":  warnings or [],
    }
