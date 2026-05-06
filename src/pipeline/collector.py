"""
collector.py - GitHub Data Collector

Fetches raw user and repository data from the GitHub API.
Returns a clean structured dict, not raw API responses.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
CACHE_DIR    = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
BASE_URL     = "https://api.github.com"

os.makedirs(CACHE_DIR, exist_ok=True)

_headers = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    _headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"


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


def _get(url: str, params: dict = None, retries: int = 3):
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
            return None

        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait  = max(reset - int(time.time()), 1)
            print(f"[collector] Rate limited. Waiting {wait}s...")
            time.sleep(wait)
            continue

        if resp.status_code == 401:
            raise RuntimeError("GitHub token is invalid or expired. Update GITHUB_TOKEN in .env")

        time.sleep(2 ** attempt)

    raise RuntimeError(f"GitHub API failed after {retries} retries for: {url}")


def fetch_github_data(username: str, use_cache: bool = True) -> dict:
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")

    cache_key = f"{username}_raw"
    if use_cache:
        cached = _load_cache(cache_key)
        if cached:
            return cached

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

    repos = []
    page  = 1
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
                "language":   r.get("language"),
                "created_at": r.get("created_at", ""),
                "updated_at": r.get("updated_at", ""),
                "topics":     r.get("topics", []) or [],
            })
        if len(batch) < 100:
            break
        page += 1

    # Fetch per-repo language byte counts (top 30 repos by stars for speed)
    # GitHub's /repos/{owner}/{repo}/languages returns { "Python": 12345, ... }
    top_repos = sorted(repos, key=lambda r: r["stars"], reverse=True)[:30]
    for r in top_repos:
        lang_data = _get(f"{BASE_URL}/repos/{username}/{r['name']}/languages")
        r["language_bytes"] = lang_data if isinstance(lang_data, dict) else {}

    result = {"user": user, "repos": repos}
    _save_cache(cache_key, result)
    return result
