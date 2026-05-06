"""
contribution_model.py - Contribution Model (Unsupervised Clustering)

Input  : repo_count, stars_per_repo, growth_rate, account_age_days,
         activity_ratio, repo_per_year, total_stars, avg_stars_per_repo
Output : contribution_style

Improvements for generalization:
  - Expanded feature set (8 features vs 6)
  - Optimal k search (3-5)
  - RobustScaler instead of StandardScaler (handles outliers better)
  - Better cluster interpretation using multiple centroid signals
"""

import numpy as np
import joblib
import os
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

from .preprocessing import (
    CONTRIBUTION_FEATURES, log_transform, extract, extract_batch,
)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "contribution_model.pkl"
)

K_RANGE = range(3, 6)


def _interpret(centers: np.ndarray) -> dict:
    """
    Rank clusters by a composite activity score.
    CONTRIBUTION_FEATURES order:
      repo_count(0), stars_per_repo(1), growth_rate(2), account_age_days(3),
      activity_ratio(4), repo_per_year(5), total_stars(6), avg_stars_per_repo(7)
    """
    # Composite: growth + activity + repo velocity + star signal
    score = (
        centers[:, 2] * 0.30 +   # growth_rate
        centers[:, 5] * 0.25 +   # repo_per_year
        centers[:, 4] * 0.20 +   # activity_ratio
        centers[:, 1] * 0.15 +   # stars_per_repo
        centers[:, 0] * 0.10     # repo_count
    )
    ranking = np.argsort(score)[::-1]
    labels  = ["Consistent Developer", "Fast Builder", "Low Activity Developer"]
    # If k > 3, extra clusters get the closest label
    result  = {}
    for rank, cid in enumerate(ranking):
        result[int(cid)] = labels[min(rank, len(labels) - 1)]
    return result


def train(feature_rows: list) -> dict:
    X_raw = extract_batch(feature_rows, CONTRIBUTION_FEATURES)
    X_log = log_transform(X_raw)

    # RobustScaler handles the heavy-tailed distributions in GitHub data better
    scaler = RobustScaler()
    X      = scaler.fit_transform(X_log)

    best_k, best_sil, best_model, best_labels = 3, -1, None, None
    for k in K_RANGE:
        m   = KMeans(n_clusters=k, random_state=42, n_init=20, max_iter=500)
        lbl = m.fit_predict(X)
        sil = silhouette_score(X, lbl)
        db  = davies_bouldin_score(X, lbl)
        print(f"  [Contribution] k={k}  silhouette={sil:.3f}  davies_bouldin={db:.3f}")
        if sil > best_sil:
            best_k, best_sil, best_model, best_labels = k, sil, m, lbl

    print(f"  [Contribution] Best k={best_k}  Silhouette={best_sil:.3f}")

    label_map = _interpret(best_model.cluster_centers_)
    print(f"  [Contribution] Cluster map: {label_map}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": best_model, "scaler": scaler, "label_map": label_map}, MODEL_PATH)

    return {"scaler": scaler, "metrics": {"silhouette": float(best_sil), "k": best_k}}


def predict(features: dict) -> dict:
    artifact  = joblib.load(MODEL_PATH)
    model     = artifact["model"]
    scaler    = artifact["scaler"]
    label_map = artifact["label_map"]

    X   = scaler.transform(log_transform(extract(features, CONTRIBUTION_FEATURES)))
    cid = int(model.predict(X)[0])

    return {"contribution_style": label_map.get(cid, "Unknown")}
