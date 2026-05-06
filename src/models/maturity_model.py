"""
maturity_model.py - Maturity Model (Regression)

Target : log(account_age_days) — held out, not in features
Output : maturity_score (0-100)

Improvements for generalization:
  - GradientBoostingRegressor instead of RandomForest (lower variance)
  - Expanded feature set (9 features vs 6)
  - Cross-validated R2 for unbiased evaluation
  - Huber loss for robustness to outliers
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_error

from .preprocessing import (
    MATURITY_FEATURES, log_transform, extract, extract_batch,
)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "maturity_model.pkl"
)


def train(feature_rows: list) -> dict:
    y = np.log1p([r.get("account_age_days", 1) for r in feature_rows])

    X_raw = extract_batch(feature_rows, MATURITY_FEATURES)
    X_log = log_transform(X_raw)

    scaler = StandardScaler()
    X      = scaler.fit_transform(X_log)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    # Huber loss is robust to the outlier developers (e.g. accounts with 0 repos but old)
    model = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        min_samples_leaf=5,
        max_features="sqrt",
        loss="huber",
        random_state=42,
    )
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    r2     = r2_score(y_te, y_pred)
    mae    = mean_absolute_error(y_te, y_pred)

    # Cross-validated R2 for unbiased generalization estimate
    cv_r2 = cross_val_score(
        model, X, y,
        cv=KFold(n_splits=5, shuffle=True, random_state=42),
        scoring="r2"
    )

    print(f"  [Maturity] R2 (test)     : {r2:.3f}")
    print(f"  [Maturity] MAE           : {mae:.3f}")
    print(f"  [Maturity] R2 (cv5)      : {cv_r2.mean():.3f} +/- {cv_r2.std():.3f}")

    all_preds     = model.predict(X).reshape(-1, 1)
    output_scaler = MinMaxScaler(feature_range=(0, 100))
    output_scaler.fit(all_preds)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({
        "model":         model,
        "scaler":        scaler,
        "output_scaler": output_scaler,
    }, MODEL_PATH)

    return {"scaler": scaler, "metrics": {"r2": float(r2), "mae": float(mae), "cv_r2": float(cv_r2.mean())}}


def predict(features: dict) -> dict:
    artifact      = joblib.load(MODEL_PATH)
    model         = artifact["model"]
    scaler        = artifact["scaler"]
    output_scaler = artifact["output_scaler"]

    X        = scaler.transform(log_transform(extract(features, MATURITY_FEATURES)))
    raw_pred = model.predict(X).reshape(-1, 1)
    score    = float(output_scaler.transform(raw_pred)[0][0])

    return {"maturity_score": round(max(0.0, min(100.0, score)), 2)}
