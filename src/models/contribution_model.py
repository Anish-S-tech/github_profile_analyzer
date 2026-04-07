"""
contribution_model.py — Contribution Model (Unsupervised Clustering)

Input  : repo_count, stars_per_repo, growth_rate,
         account_age_days, activity_ratio, repo_per_year
Output : contribution_style
"""

import numpy as np
import joblib
import os
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from .preprocessing import (
    CONTRIBUTION_FEATURES, log_transform, extract, extract_batch,
)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "contribution_model.pkl"
)

N_CLUSTERS = 3


def _interpret(centers: np.ndarray) -> dict:
    """
    Assign labels by centroid ranking.
    CONTRIBUTION_FEATURES: repo_count(0), stars_per_repo(1), growth_rate(2),
                           account_age_days(3), activity_ratio(4), repo_per_year(5)
    """
    # Score = growth_rate + repo_per_year + activity_ratio
    score = centers[:, 2] + centers[:, 5] + centers[:, 4]
    ranking = np.argsort(score)[::-1]
    labels  = ["Consistent Developer", "Fast Builder", "Low Activity Developer"]
    return {int(cluster_id): labels[rank] for rank, cluster_id in enumerate(ranking)}


# ── Training ──────────────────────────────────────────────────────────────────

def train(feature_rows: list) -> dict:
    X_raw = extract_batch(feature_rows, CONTRIBUTION_FEATURES)
    X_log = log_transform(X_raw)

    scaler = StandardScaler()
    X      = scaler.fit_transform(X_log)

    model  = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20, max_iter=500)
    labels = model.fit_predict(X)

    sil = silhouette_score(X, labels)
    print(f"  [Contribution] Silhouette Score : {sil:.3f}")

    label_map = _interpret(model.cluster_centers_)
    print(f"  [Contribution] Cluster map      : {label_map}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": model, "scaler": scaler, "label_map": label_map}, MODEL_PATH)

    return {"scaler": scaler, "metrics": {"silhouette": float(sil)}}


# ── Inference ─────────────────────────────────────────────────────────────────

def predict(features: dict) -> dict:
    artifact  = joblib.load(MODEL_PATH)
    model     = artifact["model"]
    scaler    = artifact["scaler"]
    label_map = artifact["label_map"]

    X   = scaler.transform(log_transform(extract(features, CONTRIBUTION_FEATURES)))
    cid = int(model.predict(X)[0])

    return {"contribution_style": label_map.get(cid, "Unknown")}
