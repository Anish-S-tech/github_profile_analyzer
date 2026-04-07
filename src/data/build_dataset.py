"""
build_dataset.py — Real GitHub Dataset Builder

Fetches real GitHub users via the GitHub Search API,
runs each through the Phase 1 pipeline,
and saves a clean feature dataset as JSON.

Strategy:
    Search across different follower ranges for a balanced mix:
      - Beginners   (1-9 followers)
      - Growing     (10-99 followers)
      - Advanced    (100-9999 followers)
      - High Impact (10000+ followers)

Output:
    data/raw/dataset.json       — list of feature dicts
    data/raw/dataset_meta.json  — stats about the dataset

Usage:
    python -m src.data.build_dataset
"""

import sys
import os
import json
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.pipeline.pipeline import run as pipeline_run

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

DATASET_PATH      = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "dataset.json")
DATASET_META_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "dataset_meta.json")

# Balanced buckets across follower ranges
SEARCH_BUCKETS = [
    ("followers:10000..1000000 repos:>10", 80),
    ("followers:1000..9999 repos:>5",      120),
    ("followers:100..999 repos:>3",        150),
    ("followers:10..99 repos:>1",          100),
    ("followers:1..9 repos:>1",            50),
]


def search_users(query: str, max_count: int) -> list:
    usernames = []
    page = 1

    while len(usernames) < max_count:
        try:
            resp = requests.get(
                "https://api.github.com/search/users",
                headers=HEADERS,
                params={"q": query, "per_page": 30, "page": page},
                timeout=15,
            )
        except requests.exceptions.RequestException as e:
            print(f"  [search] Network error: {e}")
            break

        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait  = max(reset - int(time.time()), 1)
            print(f"  [search] Rate limited. Waiting {wait}s...")
            time.sleep(wait)
            continue

        if resp.status_code != 200:
            print(f"  [search] HTTP {resp.status_code}")
            break

        items = resp.json().get("items", [])
        if not items:
            break

        for item in items:
            login = item.get("login", "")
            if login:
                usernames.append(login)
            if len(usernames) >= max_count:
                break

        if len(items) < 30:
            break

        page += 1
        time.sleep(0.5)

    return usernames


def main():
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)

    print("\n" + "="*60)
    print("  DATASET BUILDER")
    print("="*60)

    # Step 1 — Collect usernames
    all_usernames = []
    seen = set()

    for query, max_count in SEARCH_BUCKETS:
        print(f"\n  Searching: {query!r}  (target: {max_count})")
        found = search_users(query, max_count)
        new   = [u for u in found if u not in seen]
        seen.update(new)
        all_usernames.extend(new)
        print(f"  Found {len(new)} new  (total: {len(all_usernames)})")

    print(f"\n  Total unique usernames: {len(all_usernames)}")

    # Step 2 — Run Phase 1 pipeline
    print("\n  Running Phase 1 pipeline...")
    dataset = []
    failed  = 0

    for i, username in enumerate(all_usernames, 1):
        try:
            result = pipeline_run(username, use_cache=True)
            entry  = {"username": result["username"], **result["features"]}
            dataset.append(entry)
        except (ValueError, RuntimeError):
            failed += 1

        if i % 50 == 0 or i == len(all_usernames):
            print(f"  Processed {i}/{len(all_usernames)}  ok={len(dataset)}  failed={failed}")

    # Step 3 — Save dataset
    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    # Step 4 — Save metadata
    follower_vals = sorted([r["followers"] for r in dataset])
    n = len(follower_vals)
    meta = {
        "total_users":  n,
        "failed":       failed,
        "follower_stats": {
            "min":  follower_vals[0],
            "max":  follower_vals[-1],
            "mean": round(sum(follower_vals) / n, 1),
            "p25":  follower_vals[n // 4],
            "p75":  follower_vals[3 * n // 4],
        },
        "feature_keys": list(dataset[0].keys()) if dataset else [],
    }

    with open(DATASET_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\n" + "="*60)
    print(f"  Saved  -> data/raw/dataset.json")
    print(f"  Users  : {n}")
    print(f"  Failed : {failed}")
    print(f"  Followers range: {follower_vals[0]} - {follower_vals[-1]}")
    print(f"  Mean followers : {meta['follower_stats']['mean']}")
    print("="*60)


if __name__ == "__main__":
    main()
