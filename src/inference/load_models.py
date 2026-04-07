"""
load_models.py — Model Loader

Loads all trained models + scalers into memory once.
All other inference components import from here.

Raises clear errors if models are missing (not trained yet).
"""

import os
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")

_PATHS = {
    "impact":       os.path.join(MODELS_DIR, "impact_model.pkl"),
    "skill":        os.path.join(MODELS_DIR, "skill_model.pkl"),
    "contribution": os.path.join(MODELS_DIR, "contribution_model.pkl"),
    "maturity":     os.path.join(MODELS_DIR, "maturity_model.pkl"),
    "scalers":      os.path.join(MODELS_DIR, "scalers.pkl"),
}

# Module-level cache — loaded once, reused on every request
_cache: dict = {}


def load_all() -> dict:
    """
    Load all models and scalers into memory.
    Returns a dict with keys: impact, skill, contribution, maturity, scalers.
    Subsequent calls return the cached version instantly.
    """
    global _cache
    if _cache:
        return _cache

    missing = [name for name, path in _PATHS.items() if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError(
            f"Missing model files: {missing}. "
            f"Run 'python -m src.models.train_all' first."
        )

    _cache = {name: joblib.load(path) for name, path in _PATHS.items()}
    return _cache


def get_model(name: str):
    """Convenience accessor for a single model."""
    return load_all()[name]
