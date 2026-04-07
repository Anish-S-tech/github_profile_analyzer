"""
predictor.py — Core Predictor

Runs each of the 4 models on a feature dict.
Uses IDENTICAL preprocessing to training (same feature order, log, scale).
"""

import numpy as np
from sklearn.preprocessing import normalize

from .load_models import load_all
from src.models.preprocessing import (
    IMPACT_FEATURES, CONTRIBUTION_FEATURES, MATURITY_FEATURES,
    log_transform, extract,
)

# Skill model constants (must match skill_model.py)
_DEFAULT_SKILL = "Multi-stack Developer"


def _run_impact(features: dict, models: dict) -> dict:
    model  = models["impact"]
    scaler = models["scalers"]["impact"]

    X    = scaler.transform(log_transform(extract(features, IMPACT_FEATURES)))
    prob = float(model.predict_proba(X)[0][1])

    return {
        "impact_score":       round(prob * 100, 2),
        "impact_probability": round(prob, 4),
    }


def _run_skill(features: dict, models: dict) -> dict:
    artifact  = models["skill"]
    sk_model  = artifact["model"]
    vocab     = artifact["vocab"]
    label_map = artifact["label_map"]

    lang_dict    = features.get("languages", {})
    top_language = max(lang_dict, key=lang_dict.get) if lang_dict else "General Developer"

    if not lang_dict:
        return {"skill_type": _DEFAULT_SKILL, "top_language": top_language}

    vec = np.array([[lang_dict.get(l, 0.0) for l in vocab]], dtype=np.float64)
    vec = normalize(vec, norm="l2")
    cid = int(sk_model.predict(vec)[0])

    return {
        "skill_type":  label_map.get(cid, _DEFAULT_SKILL),
        "top_language": top_language,
    }


def _run_contribution(features: dict, models: dict) -> dict:
    artifact  = models["contribution"]
    model     = artifact["model"]
    scaler    = artifact["scaler"]
    label_map = artifact["label_map"]

    X   = scaler.transform(log_transform(extract(features, CONTRIBUTION_FEATURES)))
    cid = int(model.predict(X)[0])

    return {"contribution_type": label_map.get(cid, "Unknown")}


def _run_maturity(features: dict, models: dict) -> dict:
    artifact      = models["maturity"]
    model         = artifact["model"]
    scaler        = artifact["scaler"]
    output_scaler = artifact["output_scaler"]

    X        = scaler.transform(log_transform(extract(features, MATURITY_FEATURES)))
    raw_pred = model.predict(X).reshape(-1, 1)
    score    = float(output_scaler.transform(raw_pred)[0][0])

    return {"maturity_score": round(max(0.0, min(100.0, score)), 2)}


def run_all(features: dict) -> dict:
    """
    Run all 4 models on a single feature dict.
    Returns flat dict of all model outputs.
    """
    models = load_all()
    result = {}
    result.update(_run_impact(features, models))
    result.update(_run_skill(features, models))
    result.update(_run_contribution(features, models))
    result.update(_run_maturity(features, models))
    return result
