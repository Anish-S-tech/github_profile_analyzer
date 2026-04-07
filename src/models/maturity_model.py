"""
maturity_model.py — Maturity Model (Regression)

Target : log(account_age_days) — held out, not in features
Input  : total_stars, total_forks, repo_count,
         stars_per_repo, avg_stars_per_repo, topic_diversity
Output : maturity_score (0-100)

Rationale:
    A developer with many stars/forks but a young account is
    "punching above their weight" — high maturity score.
    The model learns this relationship without leaking age into features.
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

from .preprocessing import (
    MATURITY_FEATURES, log_transform, extract, extract_batch,
)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "maturity_model.pkl"
)


# ── Training ──────────────────────────────────────────────────────────────────

def train(feature_rows: list) -> dict:
    # Target: log(account_age_days) — not in MATURITY_FEATURES
    y = np.log1p([r.get("account_age_days", 1) for r in feature_rows])

    X_raw = extract_batch(feature_rows, MATURITY_FEATURES)
    X_log = log_transform(X_raw)

    scaler = StandardScaler()
    X      = scaler.fit_transform(X_log)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    r2  = r2_score(y_te, y_pred)
    mae = mean_absolute_error(y_te, y_pred)
    print(f"  [Maturity] R2  : {r2:.3f}")
    print(f"  [Maturity] MAE : {mae:.3f}")

    # Scale all predictions to 0-100 for readability
    all_preds      = model.predict(X).reshape(-1, 1)
    output_scaler  = MinMaxScaler(feature_range=(0, 100))
    output_scaler.fit(all_preds)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({
        "model":         model,
        "scaler":        scaler,
        "output_scaler": output_scaler,
    }, MODEL_PATH)

    return {"scaler": scaler, "metrics": {"r2": float(r2), "mae": float(mae)}}


# ── Inference ─────────────────────────────────────────────────────────────────

def predict(features: dict) -> dict:
    artifact      = joblib.load(MODEL_PATH)
    model         = artifact["model"]
    scaler        = artifact["scaler"]
    output_scaler = artifact["output_scaler"]

    X        = scaler.transform(log_transform(extract(features, MATURITY_FEATURES)))
    raw_pred = model.predict(X).reshape(-1, 1)
    score    = float(output_scaler.transform(raw_pred)[0][0])

    return {"maturity_score": round(score, 2)}
