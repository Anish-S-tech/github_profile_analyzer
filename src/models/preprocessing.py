"""
preprocessing.py — Shared Preprocessing

Single source of truth for:
  - Feature name lists (used identically in training AND inference)
  - Log transform
  - Feature extraction from dicts
  - Scaler save/load
"""

import numpy as np
import joblib
import os

SCALERS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "scalers.pkl"
)

# ── Feature sets ──────────────────────────────────────────────────────────────
# followers is intentionally EXCLUDED from IMPACT_FEATURES (used as label)
# account_age_days is intentionally EXCLUDED from MATURITY_FEATURES (used as target)

IMPACT_FEATURES = [
    "total_stars", "total_forks", "stars_per_repo",
    "growth_rate", "ff_ratio", "repo_count",
    "avg_stars_per_repo", "avg_forks_per_repo",
]

CONTRIBUTION_FEATURES = [
    "repo_count", "stars_per_repo", "growth_rate",
    "account_age_days", "activity_ratio", "repo_per_year",
]

MATURITY_FEATURES = [
    "total_stars", "total_forks", "repo_count",
    "stars_per_repo", "avg_stars_per_repo", "topic_diversity",
]

# ── Transforms ────────────────────────────────────────────────────────────────

def log_transform(X: np.ndarray) -> np.ndarray:
    return np.log1p(np.clip(X, 0, None))


def extract(features: dict, keys: list) -> np.ndarray:
    """Single feature dict → (1, F) array."""
    row = [float(features.get(k, 0)) for k in keys]
    return np.array(row, dtype=np.float64).reshape(1, -1)


def extract_batch(rows: list, keys: list) -> np.ndarray:
    """List of feature dicts → (N, F) array."""
    return np.array(
        [[float(r.get(k, 0)) for k in keys] for r in rows],
        dtype=np.float64,
    )


# ── Scaler persistence ────────────────────────────────────────────────────────

def save_scalers(scalers: dict) -> None:
    os.makedirs(os.path.dirname(SCALERS_PATH), exist_ok=True)
    joblib.dump(scalers, SCALERS_PATH)
    print(f"  Scalers saved -> models/scalers.pkl")


def load_scalers() -> dict:
    if not os.path.exists(SCALERS_PATH):
        raise FileNotFoundError("scalers.pkl not found. Run train_all.py first.")
    return joblib.load(SCALERS_PATH)
