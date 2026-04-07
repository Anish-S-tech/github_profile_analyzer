"""
impact_model.py — Impact Model (Supervised Classification)

Label  : top 25% by followers = High Impact (followers is NOT a feature)
Output : impact_score (0-100), impact_probability, impact_level
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

from .preprocessing import (
    IMPACT_FEATURES, log_transform, extract, extract_batch,
    save_scalers, load_scalers,
)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "impact_model.pkl"
)

LEVELS = [
    (0.00, 0.25, "Beginner"),
    (0.25, 0.50, "Growing"),
    (0.50, 0.80, "Advanced"),
    (0.80, 1.01, "High Impact"),
]


def _level(prob: float) -> str:
    for lo, hi, label in LEVELS:
        if lo <= prob < hi:
            return label
    return "High Impact"


# ── Training ──────────────────────────────────────────────────────────────────

def train(feature_rows: list) -> dict:
    # Label: top 25% followers = 1
    followers = np.array([r.get("followers", 0) for r in feature_rows])
    threshold = np.percentile(followers, 75)
    y = (followers >= threshold).astype(int)

    print(f"  [Impact] Label threshold : {threshold:.0f} followers")
    print(f"  [Impact] High Impact     : {y.sum()} / {len(y)}")

    X_raw = extract_batch(feature_rows, IMPACT_FEATURES)
    X_log = log_transform(X_raw)

    scaler = StandardScaler()
    X = scaler.fit_transform(X_log)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    cv  = cross_val_score(model, X, y, cv=5, scoring="roc_auc")

    print(f"  [Impact] Accuracy        : {acc:.3f}")
    print(f"  [Impact] ROC-AUC (cv5)   : {cv.mean():.3f} +/- {cv.std():.3f}")
    print(classification_report(y_te, y_pred,
                                 target_names=["Standard", "High Impact"]))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return {"scaler": scaler, "metrics": {"accuracy": acc, "roc_auc": float(cv.mean())}}


# ── Inference ─────────────────────────────────────────────────────────────────

def predict(features: dict) -> dict:
    model  = joblib.load(MODEL_PATH)
    scaler = load_scalers()["impact"]

    X = scaler.transform(log_transform(extract(features, IMPACT_FEATURES)))
    prob  = float(model.predict_proba(X)[0][1])
    score = round(prob * 100, 2)

    return {
        "impact_score":       score,
        "impact_probability": round(prob, 4),
        "impact_level":       _level(prob),
    }
