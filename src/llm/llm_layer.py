"""
llm_layer.py — LLM Layer Orchestrator

Single entry point for Phase 4.
Takes Phase 3 analysis dict → returns structured insights dict.

Usage:
    from src.llm.llm_layer import generate_insights

    insights = generate_insights(analysis)
    # {
    #     "summary":     "...",
    #     "strengths":   [...],
    #     "weaknesses":  [...],
    #     "suggestions": [...],
    #     "growth_plan": "..."
    # }
"""

from .prompt_builder  import build   as build_prompt
from .llm_engine      import call    as llm_call
from .response_parser import parse   as parse_response


def generate_insights(analysis: dict) -> dict:
    """
    Input : Phase 3 analysis dict (from src.inference.pipeline.analyze)
    Output: structured insights dict

    Always returns a valid dict — never raises.
    """
    prompt   = build_prompt(analysis)
    raw_text = llm_call(prompt)
    insights = parse_response(raw_text)
    return insights
