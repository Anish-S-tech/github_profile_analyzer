"""
test_inference.py — Phase 3 End-to-End Tests

Tests the full inference pipeline on:
  - Beginner   : Bhuvanesh3602
  - Intermediate: karpathy
  - Famous     : torvalds
  - Edge case  : invalid username
  - Edge case  : user with 0 repos (mocked via Phase 1 cleaner)
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.inference.pipeline      import analyze
from src.inference.postprocessing import build_output

REQUIRED_KEYS = {
    "username", "profile", "metrics", "languages", "warnings"
}
REQUIRED_PROFILE_KEYS = {
    "followers", "following", "repo_count",
    "total_stars", "total_forks", "top_language", "account_age_days",
}
REQUIRED_METRICS_KEYS = {
    "impact_score", "impact_probability", "impact_level",
    "skill_type", "contribution_type",
    "maturity_score", "maturity_level",
}


def assert_valid_result(result: dict, label: str):
    assert "error" not in result, f"[{label}] Got error: {result['error']}"

    missing_top = REQUIRED_KEYS - set(result.keys())
    assert not missing_top, f"[{label}] Missing top-level keys: {missing_top}"

    missing_profile = REQUIRED_PROFILE_KEYS - set(result["profile"].keys())
    assert not missing_profile, f"[{label}] Missing profile keys: {missing_profile}"

    missing_metrics = REQUIRED_METRICS_KEYS - set(result["metrics"].keys())
    assert not missing_metrics, f"[{label}] Missing metrics keys: {missing_metrics}"

    m = result["metrics"]
    assert 0 <= m["impact_score"]       <= 100, f"[{label}] impact_score out of range"
    assert 0 <= m["impact_probability"] <= 1,   f"[{label}] impact_probability out of range"
    assert 0 <= m["maturity_score"]     <= 100, f"[{label}] maturity_score out of range"
    assert m["impact_level"]   in {"Beginner", "Growing", "Advanced", "High Impact"}
    assert m["maturity_level"] in {"Early Stage", "Developing", "Experienced", "Expert"}


def print_result(result: dict):
    p = result["profile"]
    m = result["metrics"]
    print(f"    followers       : {p['followers']}")
    print(f"    repo_count      : {p['repo_count']}")
    print(f"    top_language    : {p['top_language']}")
    print(f"    impact_score    : {m['impact_score']}  ({m['impact_level']})")
    print(f"    skill_type      : {m['skill_type']}")
    print(f"    contribution    : {m['contribution_type']}")
    print(f"    maturity_score  : {m['maturity_score']}  ({m['maturity_level']})")
    print(f"    warnings        : {result['warnings'] or 'none'}")


def run_test(label: str, username: str) -> bool:
    print(f"\n  {'='*54}")
    print(f"  {label} -> @{username}")
    print(f"  {'='*54}")
    try:
        result = analyze(username, use_cache=True)
        assert_valid_result(result, label)
        print_result(result)
        print(f"  PASS")
        return True
    except AssertionError as e:
        print(f"  FAIL (assertion): {e}")
        return False
    except Exception as e:
        print(f"  FAIL (exception): {e}")
        return False


def test_invalid_username() -> bool:
    print(f"\n  {'='*54}")
    print(f"  Edge Case -> invalid username")
    print(f"  {'='*54}")
    result = analyze("this_user_xyz_does_not_exist_abc123", use_cache=False)
    if "error" in result:
        print(f"  Correctly returned error: {result['error']}")
        print(f"  PASS")
        return True
    print(f"  FAIL — expected error, got: {result}")
    return False


def test_zero_repos() -> bool:
    """Mock a user with 0 repos directly through postprocessing."""
    print(f"\n  {'='*54}")
    print(f"  Edge Case -> user with 0 repos (mocked)")
    print(f"  {'='*54}")
    try:
        mock_features = {
            "followers": 0, "following": 0, "repo_count": 0,
            "total_stars": 0, "total_forks": 0,
            "avg_stars_per_repo": 0.0, "avg_forks_per_repo": 0.0,
            "account_age_days": 365, "growth_rate": 0.0,
            "repo_per_year": 0.0, "activity_ratio": 0.0,
            "ff_ratio": 0.0, "stars_per_repo": 0.0,
            "languages": {}, "unique_languages": 0,
            "active_repo_count": 0, "topic_diversity": 0,
            "avg_repo_age_days": 0.0,
        }
        from src.inference.predictor import run_all
        predictions = run_all(mock_features)
        result = build_output("ghost_user", mock_features, predictions, ["No repos"])

        assert result["metrics"]["impact_score"]   >= 0
        assert result["metrics"]["maturity_score"] >= 0
        assert result["languages"] == {}
        print(f"    impact_score   : {result['metrics']['impact_score']}")
        print(f"    maturity_score : {result['metrics']['maturity_score']}")
        print(f"    skill_type     : {result['metrics']['skill_type']}")
        print(f"  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*58)
    print("  PHASE 3 — INFERENCE ENGINE TESTS")
    print("="*58)

    results = [
        run_test("Beginner",     "Bhuvanesh3602"),
        run_test("Intermediate", "karpathy"),
        run_test("Famous Dev",   "torvalds"),
        test_invalid_username(),
        test_zero_repos(),
    ]

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*58}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*58}")
    sys.exit(0 if passed == total else 1)
