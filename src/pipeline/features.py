"""
features.py — Feature Engineering Layer

Converts cleaned GitHub data into a structured, ML-ready feature vector.

Output shape:
{
    # Profile
    "followers":          int,
    "following":          int,
    "repo_count":         int,

    # Repository aggregates
    "total_stars":        int,
    "total_forks":        int,
    "avg_stars_per_repo": float,
    "avg_forks_per_repo": float,

    # Growth & activity
    "account_age_days":   int,
    "growth_rate":        float,   # followers / age_days
    "repo_per_year":      float,   # repos / age_years
    "activity_ratio":     float,   # recently updated repos / total repos

    # Ratios
    "ff_ratio":           float,   # followers / (following + 1)
    "stars_per_repo":     float,   # total_stars / (repo_count + 1)

    # Language distribution  { "Python": 0.5, "JavaScript": 0.3, ... }
    "languages":          dict[str, float],

    # Diversity
    "unique_languages":   int,
    "active_repo_count":  int,     # repos updated in last 365 days

    # Advanced
    "topic_diversity":    int,     # total unique topics across all repos
    "avg_repo_age_days":  float,   # avg age of repos
}
"""

from datetime import datetime, timezone, timedelta


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(iso: str):
    """Parse ISO date string → aware datetime. Returns None if invalid."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_since(iso: str) -> int:
    dt = _parse_date(iso)
    if dt is None:
        return 0
    return max((_now() - dt).days, 0)


# ── Public API ────────────────────────────────────────────────────────────────

def build_features(cleaned: dict) -> dict:
    """
    Input:  cleaned dict from cleaner.clean()
    Output: flat feature dict ready for ML consumption

    Always returns a complete dict — no missing keys, no None values.
    """
    user  = cleaned.get("user", {})
    repos = cleaned.get("repos", [])

    # ── A. Profile-level ─────────────────────────────────────────────────────
    followers  = user.get("followers", 0)
    following  = user.get("following", 0)
    repo_count = len(repos)

    # ── B. Repository aggregates ──────────────────────────────────────────────
    total_stars = sum(r["stars"] for r in repos)
    total_forks = sum(r["forks"] for r in repos)
    avg_stars_per_repo = total_stars / (repo_count + 1)
    avg_forks_per_repo = total_forks / (repo_count + 1)

    # ── C. Growth & activity ──────────────────────────────────────────────────
    account_age_days = _days_since(user.get("created_at", ""))
    account_age_days = max(account_age_days, 1)   # avoid division by zero

    growth_rate  = followers / account_age_days
    repo_per_year = repo_count / (account_age_days / 365 + 1)

    cutoff = _now() - timedelta(days=365)
    active_repos = [
        r for r in repos
        if _parse_date(r.get("updated_at", "")) and
           _parse_date(r["updated_at"]) >= cutoff
    ]
    active_repo_count = len(active_repos)
    activity_ratio = active_repo_count / (repo_count + 1)

    # ── D. Ratio features ─────────────────────────────────────────────────────
    ff_ratio      = followers / (following + 1)
    stars_per_repo = total_stars / (repo_count + 1)

    # ── E. Language distribution ──────────────────────────────────────────────
    lang_counts: dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if lang and lang.strip():         # skip None / empty / whitespace
            lang_counts[lang.strip()] = lang_counts.get(lang.strip(), 0) + 1

    # Fallback: scan topics for language hints if no language data found
    if not lang_counts:
        TOPIC_LANG_MAP = {
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
            "java": "Java", "cpp": "C++", "c-plus-plus": "C++", "c": "C",
            "rust": "Rust", "go": "Go", "golang": "Go", "ruby": "Ruby",
            "php": "PHP", "swift": "Swift", "kotlin": "Kotlin", "dart": "Dart",
            "html": "HTML", "css": "CSS", "shell": "Shell", "r": "R",
        }
        for r in repos:
            for topic in r.get("topics", []):
                mapped = TOPIC_LANG_MAP.get(topic.lower())
                if mapped:
                    lang_counts[mapped] = lang_counts.get(mapped, 0) + 1

    total_lang_repos = sum(lang_counts.values())
    languages: dict[str, float] = {
        lang: round(count / total_lang_repos, 4)
        for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1])
    } if total_lang_repos > 0 else {}

    unique_languages = len(lang_counts)

    # ── F. Diversity features ─────────────────────────────────────────────────
    all_topics: set[str] = set()
    for r in repos:
        all_topics.update(r.get("topics", []))
    topic_diversity = len(all_topics)

    # ── G. Avg repo age ───────────────────────────────────────────────────────
    repo_ages = [_days_since(r.get("created_at", "")) for r in repos]
    avg_repo_age_days = sum(repo_ages) / len(repo_ages) if repo_ages else 0.0

    return {
        # Profile
        "followers":          followers,
        "following":          following,
        "repo_count":         repo_count,
        # Repo aggregates
        "total_stars":        total_stars,
        "total_forks":        total_forks,
        "avg_stars_per_repo": round(avg_stars_per_repo, 4),
        "avg_forks_per_repo": round(avg_forks_per_repo, 4),
        # Growth & activity
        "account_age_days":   account_age_days,
        "growth_rate":        round(growth_rate, 6),
        "repo_per_year":      round(repo_per_year, 4),
        "activity_ratio":     round(activity_ratio, 4),
        # Ratios
        "ff_ratio":           round(ff_ratio, 4),
        "stars_per_repo":     round(stars_per_repo, 4),
        # Language distribution
        "languages":          languages,
        # Diversity
        "unique_languages":   unique_languages,
        "active_repo_count":  active_repo_count,
        # Advanced
        "topic_diversity":    topic_diversity,
        "avg_repo_age_days":  round(avg_repo_age_days, 2),
    }
