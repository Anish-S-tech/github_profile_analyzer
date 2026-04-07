"""
collector.py — GitHub Data Collector

Fetches raw user and repository data from the GitHub API.
Returns a clean structured dict, not raw API responses.

Output shape:
{
    "user": {
        "username": str,
        "followers": int,
        "following": int,
        "created_at": str (ISO),
        "bio": str | None,
        "location": str | None,
    },
    "repos": [
        {
            "name": str,
            "stars": int,
            "forks": int,
            "language": str | None,
            "created_at": str (ISO),
            "updated_at": str (ISO),
            "topics": list[str],
        },
        ...
    ]
}
"""

import os
import json
import time
import requests

# ── Config ────────────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
BASE_URL = "https://api.github.com"

os.makedirs(CACHE_DIR, exist_ok=True)

_headers = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    _headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_path(key: str) -> str:
    safe = key.replace("/", "_").replace(" ", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _load_cache(key: str):
    path = _cache_path(key)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(key: str, data) -> None:
    with open(_cache_path(key), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _get(url: str, params: dict = None, retries: int = 3):
    """
    GET with automatic rate-limit handling and retries.
    Raises RuntimeError on unrecoverable failure.
    """
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=_headers, params=params, timeout=15)
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Cannot reach GitHub API. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise RuntimeError("GitHub API timed out.")

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 404:
            return None  # caller decides what 404 means

        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - int(time.time()), 1)
            print(f"[collector] Rate limited. Waiting {wait}s...")
            time.sleep(wait)
            continue

        if resp.status_code == 401:
            raise RuntimeError("GitHub token is invalid or expired.")

        # Other errors — wait and retry
        time.sleep(2 ** attempt)

    raise RuntimeError(f"GitHub API failed after {retries} retries for: {url}")


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_github_data(username: str, use_cache: bool = True) -> dict:
    """
    Main entry point. Returns structured dict with 'user' and 'repos'.
    Raises ValueError for invalid usernames.
    Raises RuntimeError for API/network failures.
    """
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")

    cache_key = f"{username}_raw"
    if use_cache:
        cached = _load_cache(cache_key)
        if cached:
            return cached

    # ── Fetch user ────────────────────────────────────────────────────────────
    raw_user = _get(f"{BASE_URL}/users/{username}")
    if raw_user is None:
        raise ValueError(f"GitHub user '{username}' not found.")

    user = {
        "username":   raw_user.get("login", username),
        "followers":  raw_user.get("followers", 0),
        "following":  raw_user.get("following", 0),
        "created_at": raw_user.get("created_at", ""),
        "bio":        raw_user.get("bio"),
        "location":   raw_user.get("location"),
    }

    # ── Fetch repos ───────────────────────────────────────────────────────────
    repos = []
    page = 1
    while True:
        batch = _get(
            f"{BASE_URL}/users/{username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        if not batch:
            break
        for r in batch:
            repos.append({
                "name":       r.get("name", ""),
                "stars":      r.get("stargazers_count", 0) or 0,
                "forks":      r.get("forks_count", 0) or 0,
                "language":   r.get("language"),          # None is valid
                "created_at": r.get("created_at", ""),
                "updated_at": r.get("updated_at", ""),
                "topics":     r.get("topics", []) or [],
            })
        if len(batch) < 100:
            break
        page += 1

    result = {"user": user, "repos": repos}
    _save_cache(cache_key, result)
    return result
