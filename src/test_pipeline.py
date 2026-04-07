"""
test_pipeline.py — Phase 1 Test Suite

Tests the full pipeline against 3 developer profiles:
  - Beginner   : low repos, low followers
  - Intermediate: moderate activity
  - Famous     : Linus Torvalds (high stars, high followers)

Also tests edge cases:
  - Invalid username
  - Username with 0 repos (mocked)
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline.pipeline import run
from src.pipeline.cleaner  import clean, validate
from src.pipeline.features import build_features

# ── Helpers ───────────────────────────────────────────────────────────────────

REQUIRED_FEATURE_KEYS = {
    "followers", "following", "repo_count",
    "total_stars", "total_forks", "avg_stars_per_repo", "avg_forks_per_repo",
    "account_age_days", "growth_rate", "repo_per_year", "activity_ratio",
    "ff_ratio", "stars_per_repo",
    "languages", "unique_languages", "active_repo_count",
    "topic_diversity", "avg_repo_age_days",
}


def assert_valid_features(features: dict, label: str):
    missing = REQUIRED_FEATURE_KEYS - set(features.keys())
    assert not missing, f"[{label}] Missing keys: {missing}"

    for key, val in features.items():
        if key == "languages":
            assert isinstance(val, dict), f"[{label}] languages must be dict"
            total = sum(val.values())
            if val:
                assert abs(total - 1.0) < 0.01, f"[{label}] language ratios must sum to 1, got {total}"
        else:
            assert val is not None, f"[{label}] {key} is None"
            assert not (isinstance(val, float) and val != val), f"[{label}] {key} is NaN"

    print(f"  ✓ All {len(REQUIRED_FEATURE_KEYS)} required keys present and valid")


def print_features(features: dict):
    flat = {k: v for k, v in features.items() if k != "languages"}
    print(json.dumps(flat, indent=4))
    print(f"  languages: {features['languages']}")


def run_test(label: str, username: str):
    print(f"\n{'='*60}")
    print(f"  TEST: {label} -> @{username}")
    print(f"{'='*60}")
    try:
        result = run(username, use_cache=True)
        print(f"  username      : {result['username']}")
        print(f"  warnings      : {result['warnings'] or 'none'}")
        assert_valid_features(result["features"], label)
        print_features(result["features"])
        return True
    except ValueError as e:
        print(f"  ✗ ValueError: {e}")
        return False
    except RuntimeError as e:
        print(f"  ✗ RuntimeError: {e}")
        return False


# ── Edge case: invalid username ───────────────────────────────────────────────

def test_invalid_username():
    print(f"\n{'='*60}")
    print(f"  TEST: Edge Case -> invalid username")
    print(f"{'='*60}")
    try:
        run("this_user_absolutely_does_not_exist_xyzxyz123", use_cache=False)
        print("  ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
        return True
    except RuntimeError as e:
        print(f"  ✓ Correctly raised RuntimeError (API down?): {e}")
        return True


# ── Edge case: zero repos (mocked) ───────────────────────────────────────────

def test_zero_repos():
    print(f"\n{'='*60}")
    print(f"  TEST: Edge Case -> user with 0 repos")
    print(f"{'='*60}")
    mock_raw = {
        "user": {
            "username":   "ghost_user",
            "followers":  0,
            "following":  0,
            "created_at": "2020-01-01T00:00:00Z",
            "bio":        None,
            "location":   None,
        },
        "repos": []
    }
    cleaned  = clean(mock_raw)
    warnings = validate(cleaned)
    features = build_features(cleaned)

    print(f"  warnings: {warnings}")
    assert_valid_features(features, "zero_repos")
    assert features["total_stars"]    == 0
    assert features["total_forks"]    == 0
    assert features["languages"]      == {}
    assert features["unique_languages"] == 0
    print("  ✓ Zero-repo edge case passed")
    return True


# ── Edge case: zero followers ─────────────────────────────────────────────────

def test_zero_followers():
    print(f"\n{'='*60}")
    print(f"  TEST: Edge Case -> user with 0 followers, 0 following")
    print(f"{'='*60}")
    mock_raw = {
        "user": {
            "username":   "new_dev",
            "followers":  0,
            "following":  0,
            "created_at": "2023-06-01T00:00:00Z",
            "bio":        None,
            "location":   None,
        },
        "repos": [
            {"name": "hello-world", "stars": 0, "forks": 0,
             "language": "Python", "created_at": "2023-06-02T00:00:00Z",
             "updated_at": "2023-06-02T00:00:00Z", "topics": []}
        ]
    }
    cleaned  = clean(mock_raw)
    features = build_features(cleaned)
    assert_valid_features(features, "zero_followers")
    assert features["ff_ratio"]    == 0.0
    assert features["growth_rate"] == 0.0
    print("  ✓ Zero-followers edge case passed")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = []

    # Real API tests
    results.append(run_test("Beginner",      "Bhuvanesh3602"))
    results.append(run_test("Intermediate",  "karpathy"))
    results.append(run_test("Famous Dev",    "torvalds"))

    # Edge case tests (no API needed)
    results.append(test_invalid_username())
    results.append(test_zero_repos())
    results.append(test_zero_followers())

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")
    sys.exit(0 if passed == total else 1)
