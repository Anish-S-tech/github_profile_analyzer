"""
test_llm.py — Phase 4 LLM Layer Tests

Tests:
  1. Prompt builder produces a filled, non-empty prompt
  2. Response parser handles valid JSON
  3. Response parser handles malformed JSON gracefully
  4. Response parser handles markdown-wrapped JSON
  5. Full LLM layer with fallback (no API key needed)
  6. Full pipeline analyze() with llm=False (structural test)
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.llm.prompt_builder  import build as build_prompt
from src.llm.response_parser import parse as parse_response
from src.llm.llm_layer       import generate_insights
from src.inference.pipeline  import analyze

REQUIRED_INSIGHT_KEYS = {"summary", "strengths", "weaknesses", "suggestions", "growth_plan"}

# ── Mock Phase 3 output ───────────────────────────────────────────────────────

MOCK_ANALYSIS = {
    "username": "testdev",
    "profile": {
        "followers": 120, "following": 30, "repo_count": 15,
        "total_stars": 300, "total_forks": 50,
        "top_language": "Python", "account_age_days": 800,
    },
    "metrics": {
        "impact_score": 32.0, "impact_probability": 0.32,
        "impact_level": "Growing",
        "skill_type": "AI / Data Developer",
        "contribution_type": "Consistent Developer",
        "maturity_score": 45.0, "maturity_level": "Developing",
    },
    "languages": {"Python": 0.6, "JavaScript": 0.3, "Shell": 0.1},
    "warnings": [],
}


def run_test(label: str, fn) -> bool:
    print(f"\n  {'='*54}")
    print(f"  {label}")
    print(f"  {'='*54}")
    try:
        fn()
        print(f"  PASS")
        return True
    except AssertionError as e:
        print(f"  FAIL (assertion): {e}")
        return False
    except Exception as e:
        print(f"  FAIL (exception): {e}")
        return False


# ── Test 1: Prompt builder ────────────────────────────────────────────────────

def test_prompt_builder():
    prompt = build_prompt(MOCK_ANALYSIS)
    assert isinstance(prompt, str) and len(prompt) > 100, "Prompt too short"
    assert "testdev"              in prompt, "username missing"
    assert "120"                  in prompt, "followers missing"
    assert "32"                   in prompt, "impact_score missing"
    assert "AI / Data Developer"  in prompt, "skill_type missing"
    assert "Python: 60.0%"        in prompt, "language distribution missing"
    print(f"    Prompt length: {len(prompt)} chars")
    print(f"    First 200 chars: {prompt[:200]}")


# ── Test 2: Parser — valid JSON ───────────────────────────────────────────────

def test_parser_valid():
    raw = json.dumps({
        "summary":     "A growing developer.",
        "strengths":   ["Good activity", "Python skills"],
        "weaknesses":  ["Low visibility"],
        "suggestions": ["Build more projects", "Contribute to OSS"],
        "growth_plan": "Focus on open source for 30 days.",
    })
    result = parse_response(raw)
    missing = REQUIRED_INSIGHT_KEYS - set(result.keys())
    assert not missing, f"Missing keys: {missing}"
    assert result["summary"] == "A growing developer."
    assert len(result["strengths"]) == 2
    print(f"    Parsed keys: {list(result.keys())}")


# ── Test 3: Parser — malformed JSON ──────────────────────────────────────────

def test_parser_malformed():
    result = parse_response("This is not JSON at all!!!")
    missing = REQUIRED_INSIGHT_KEYS - set(result.keys())
    assert not missing, f"Missing keys after malformed input: {missing}"
    assert isinstance(result["strengths"],   list)
    assert isinstance(result["suggestions"], list)
    print(f"    Graceful fallback summary: {result['summary'][:60]}")


# ── Test 4: Parser — markdown-wrapped JSON ────────────────────────────────────

def test_parser_markdown():
    raw = """```json
{
  "summary": "Strong developer.",
  "strengths": ["High stars"],
  "weaknesses": ["Few repos"],
  "suggestions": ["Add documentation"],
  "growth_plan": "Write more READMEs."
}
```"""
    result = parse_response(raw)
    assert result["summary"] == "Strong developer."
    print(f"    Correctly stripped markdown fences")


# ── Test 5: Full LLM layer (fallback — Ollama not running) ───────────────────────

def test_llm_layer_fallback():
    # Temporarily point to a port nothing is listening on to force fallback
    import src.llm.llm_engine as engine
    original_url = engine.OLLAMA_URL
    engine.OLLAMA_URL = "http://localhost:19999/api/generate"  # nothing here

    try:
        insights = generate_insights(MOCK_ANALYSIS)
        missing  = REQUIRED_INSIGHT_KEYS - set(insights.keys())
        assert not missing, f"Missing keys in fallback: {missing}"
        assert isinstance(insights["suggestions"], list)
        print(f"    Fallback summary: {insights['summary'][:80]}")
    finally:
        engine.OLLAMA_URL = original_url


# ── Test 6: Full pipeline with llm=False ─────────────────────────────────────

def test_pipeline_no_llm():
    result = analyze("karpathy", use_cache=True, llm=False)
    assert "error"    not in result,  f"Got error: {result.get('error')}"
    assert "metrics"  in result,      "Missing metrics"
    assert "profile"  in result,      "Missing profile"
    assert result["insights"] is None, "insights should be None when llm=False"
    print(f"    impact_level : {result['metrics']['impact_level']}")
    print(f"    skill_type   : {result['metrics']['skill_type']}")
    print(f"    insights     : None (llm=False, correct)")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*58)
    print("  PHASE 4 - LLM LAYER TESTS")
    print("="*58)

    results = [
        run_test("Prompt Builder",              test_prompt_builder),
        run_test("Response Parser - Valid JSON", test_parser_valid),
        run_test("Response Parser - Malformed",  test_parser_malformed),
        run_test("Response Parser - Markdown",   test_parser_markdown),
        run_test("LLM Layer - Fallback",         test_llm_layer_fallback),
        run_test("Pipeline - llm=False",         test_pipeline_no_llm),
    ]

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*58}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*58}")
    sys.exit(0 if passed == total else 1)
