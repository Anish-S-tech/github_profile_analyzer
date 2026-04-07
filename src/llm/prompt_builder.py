"""
prompt_builder.py — Prompt Builder

Converts Phase 3 structured output into a filled prompt string
ready to be sent to the LLM.

Keeps all data-injection logic in one place so the prompt
template never needs to change when data shapes change.
"""

import os

_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "prompts.txt"
)

with open(_TEMPLATE_PATH, "r", encoding="utf-8") as _f:
    _TEMPLATE = _f.read()


def _format_languages(languages: dict) -> str:
    """Convert language dict to readable bullet list."""
    if not languages:
        return "  No language data available."
    lines = [f"  {lang}: {round(ratio * 100, 1)}%" for lang, ratio in languages.items()]
    return "\n".join(lines)


def build(analysis: dict) -> str:
    """
    Input : full Phase 3 analysis dict (from src.inference.pipeline.analyze)
    Output: filled prompt string ready for the LLM
    """
    profile = analysis.get("profile", {})
    metrics = analysis.get("metrics", {})
    langs   = analysis.get("languages", {})

    return _TEMPLATE.format(
        username             = analysis.get("username", "unknown"),
        followers            = profile.get("followers", 0),
        following            = profile.get("following", 0),
        repo_count           = profile.get("repo_count", 0),
        total_stars          = profile.get("total_stars", 0),
        total_forks          = profile.get("total_forks", 0),
        top_language         = profile.get("top_language", "Unknown"),
        account_age_days     = profile.get("account_age_days", 0),
        impact_score         = metrics.get("impact_score", 0),
        impact_level         = metrics.get("impact_level", "Unknown"),
        skill_type           = metrics.get("skill_type", "Unknown"),
        contribution_type    = metrics.get("contribution_type", "Unknown"),
        maturity_score       = metrics.get("maturity_score", 0),
        maturity_level       = metrics.get("maturity_level", "Unknown"),
        language_distribution= _format_languages(langs),
    )
