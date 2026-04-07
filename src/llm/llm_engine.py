"""
llm_engine.py — LLM Engine (Ollama)

Sends a prompt to a locally running Ollama instance and returns
the raw response text.

Requirements:
    1. Ollama installed and running  →  ollama serve
    2. Model pulled                  →  ollama pull llama3.2

Config (change MODEL to any model you have pulled):
    ollama list   ← shows available models
"""

import json
import time
import requests

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "llama3.2"   # change to any model you have: mistral, gemma2, etc.
TEMPERATURE = 0.6
MAX_RETRIES = 3
RETRY_DELAY = 2            # seconds between retries
TIMEOUT     = 120          # seconds — local models can be slow on first run


# ── Engine ────────────────────────────────────────────────────────────────────

def call(prompt: str) -> str:
    """
    Send prompt to Ollama and return raw response text.

    Returns the model response string on success.
    Returns a fallback JSON string on any failure so the
    response_parser always has something to work with.
    """
    system = (
        "You are an expert GitHub mentor. "
        "Always respond with valid JSON only. "
        "No markdown, no extra text outside the JSON block."
    )

    full_prompt = f"{system}\n\n{prompt}"

    payload = {
        "model":  MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
        },
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=TIMEOUT,
            )

            if resp.status_code == 200:
                return resp.json().get("response", "").strip()

            if resp.status_code == 404:
                return _fallback(
                    f"Model '{MODEL}' not found. "
                    f"Run: ollama pull {MODEL}"
                )

            # Other HTTP errors — retry
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue

            return _fallback(f"Ollama HTTP {resp.status_code}: {resp.text[:200]}")

        except requests.exceptions.ConnectionError:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return _fallback(
                "Cannot connect to Ollama. "
                "Make sure it is running: ollama serve"
            )

        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return _fallback(
                f"Ollama timed out after {TIMEOUT}s. "
                "Try a smaller model or increase TIMEOUT."
            )

        except Exception as e:
            return _fallback(f"Unexpected error: {e}")

    return _fallback("Unknown failure in LLM engine.")


def _fallback(reason: str) -> str:
    """Return a valid JSON fallback so the parser never crashes."""
    return json.dumps({
        "summary":     f"LLM unavailable: {reason}",
        "strengths":   ["Could not generate — LLM unavailable."],
        "weaknesses":  ["Could not generate — LLM unavailable."],
        "suggestions": ["Start Ollama with: ollama serve"],
        "growth_plan": "LLM unavailable.",
    })


def check_ollama() -> dict:
    """
    Health check — returns { "ok": bool, "models": list, "message": str }
    Useful for the API layer to report LLM status.
    """
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return {"ok": True, "models": models, "message": "Ollama is running."}
        return {"ok": False, "models": [], "message": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "models": [], "message": "Ollama not running. Run: ollama serve"}
    except Exception as e:
        return {"ok": False, "models": [], "message": str(e)}
