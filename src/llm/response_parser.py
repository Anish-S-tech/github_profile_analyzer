"""
response_parser.py — Response Parser

Converts raw LLM text → clean structured dict.
Never crashes — always returns a valid output shape
even if the LLM returns malformed JSON.
"""

import json
import re


_EXPECTED_SHAPE = {
    "summary":     str,
    "strengths":   list,
    "weaknesses":  list,
    "suggestions": list,
    "growth_plan": str,
}

_FALLBACK = {
    "summary":     "Could not parse LLM response.",
    "strengths":   [],
    "weaknesses":  [],
    "suggestions": [],
    "growth_plan": "",
}


def _extract_json(text: str) -> str:
    """
    Extract the first JSON object from text.
    Handles cases where LLM wraps JSON in markdown code fences.
    """
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Find first { ... } block
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def _safe_list(value, default: list) -> list:
    """Ensure value is a list of strings."""
    if not isinstance(value, list):
        return default
    return [str(item) for item in value if item]


def _safe_str(value, default: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return default
    return value.strip()


def parse(raw_text: str) -> dict:
    """
    Input : raw string from llm_engine.call()
    Output: structured dict with keys:
            summary, strengths, weaknesses, suggestions, growth_plan
    """
    if not raw_text or not raw_text.strip():
        return _FALLBACK.copy()

    try:
        json_str = _extract_json(raw_text)
        data     = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return {**_FALLBACK, "summary": f"Parse error. Raw: {raw_text[:200]}"}

    return {
        "summary":     _safe_str(data.get("summary"),     _FALLBACK["summary"]),
        "strengths":   _safe_list(data.get("strengths"),  []),
        "weaknesses":  _safe_list(data.get("weaknesses"), []),
        "suggestions": _safe_list(data.get("suggestions"),[]),
        "growth_plan": _safe_str(data.get("growth_plan"), ""),
    }
