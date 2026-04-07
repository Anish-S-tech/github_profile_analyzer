"""
test_models.py — Phase 2 Inference Verification

Tests all 4 models end-to-end on real GitHub users:
  - torvalds   (famous, high impact)
  - karpathy   (AI researcher)
  - Bhuvanesh3602 (beginner)

Usage:
    python -m src.models.test_models
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.pipeline.pipeline import run as pipeline_run
from src.models.inference  import predict

REQUIRED_OUTPUT_KEYS = {
    "impact_score", "impact_probability", "impact_level",
    "skill_cluster", "top_language",
    "contribution_style",
    "maturity_score",
}

TEST_USERS = [
    ("torvalds",      "High Impact"),
    ("karpathy",      "High Impact"),
    ("Bhuvanesh3602", "Beginner / Growing"),
]


def run_test(username: str, expected_tier: str) -> bool:
    print(f"\n  {'='*54}")
    print(f"  User : @{username}  (expected tier: {expected_tier})")
    print(f"  {'='*54}")

    try:
        pipeline_result = pipeline_run(username, use_cache=True)
        features        = pipeline_result["features"]
        ml_result       = predict(features)

        # Check all keys present
        missing = REQUIRED_OUTPUT_KEYS - set(ml_result.keys())
        assert not missing, f"Missing output keys: {missing}"

        # Check types
        assert isinstance(ml_result["impact_score"],       float)
        assert isinstance(ml_result["impact_probability"], float)
        assert isinstance(ml_result["impact_level"],       str)
        assert isinstance(ml_result["skill_cluster"],      str)
        assert isinstance(ml_result["top_language"],       str)
        assert isinstance(ml_result["contribution_style"], str)
        assert isinstance(ml_result["maturity_score"],     float)

        # Check ranges
        assert 0 <= ml_result["impact_score"]       <= 100
        assert 0 <= ml_result["impact_probability"] <= 1
        assert 0 <= ml_result["maturity_score"]     <= 100

        print(f"  impact_score       : {ml_result['impact_score']}")
        print(f"  impact_level       : {ml_result['impact_level']}")
        print(f"  impact_probability : {ml_result['impact_probability']}")
        print(f"  skill_cluster      : {ml_result['skill_cluster']}")
        print(f"  top_language       : {ml_result['top_language']}")
        print(f"  contribution_style : {ml_result['contribution_style']}")
        print(f"  maturity_score     : {ml_result['maturity_score']}")
        print(f"  PASS")
        return True

    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def main():
    print("\n" + "="*58)
    print("  PHASE 2 — INFERENCE VERIFICATION")
    print("="*58)

    results = [run_test(u, t) for u, t in TEST_USERS]

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*58}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*58}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
