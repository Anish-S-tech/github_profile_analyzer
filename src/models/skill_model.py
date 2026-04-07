"""
skill_model.py — Skill Model (Unsupervised Clustering)

Input  : language distribution dict  { "Python": 0.5, "JS": 0.3, ... }
Output : skill_cluster, top_language
"""

import numpy as np
import joblib
import os
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "skill_model.pkl"
)

N_CLUSTERS = 5
VOCAB_SIZE  = 20

# Map dominant language → human cluster label
LANG_TO_LABEL = {
    "Python":           "AI / Data Developer",
    "Jupyter Notebook": "AI / Data Developer",
    "R":                "AI / Data Developer",
    "JavaScript":       "Web Developer",
    "TypeScript":       "Web Developer",
    "HTML":             "Web Developer",
    "CSS":              "Web Developer",
    "C":                "Systems Developer",
    "C++":              "Systems Developer",
    "Rust":             "Systems Developer",
    "Go":               "Systems Developer",
    "Assembly":         "Systems Developer",
    "Java":             "Backend Developer",
    "Kotlin":           "Backend Developer",
    "PHP":              "Backend Developer",
    "Ruby":             "Backend Developer",
    "Scala":            "Backend Developer",
    "Swift":            "Mobile Developer",
    "Dart":             "Mobile Developer",
    "Objective-C":      "Mobile Developer",
}
DEFAULT_LABEL = "Multi-stack Developer"


def _build_vocab(lang_dicts: list) -> list:
    counts = {}
    for ld in lang_dicts:
        for lang, ratio in ld.items():
            counts[lang] = counts.get(lang, 0.0) + ratio
    return sorted(counts, key=lambda l: -counts[l])[:VOCAB_SIZE]


def _vectorize_batch(lang_dicts: list, vocab: list) -> np.ndarray:
    return np.array(
        [[ld.get(lang, 0.0) for lang in vocab] for ld in lang_dicts],
        dtype=np.float64,
    )


def _interpret(center: np.ndarray, vocab: list) -> str:
    if center.sum() == 0:
        return DEFAULT_LABEL
    top_lang = vocab[int(np.argmax(center))]
    return LANG_TO_LABEL.get(top_lang, DEFAULT_LABEL)


# ── Training ──────────────────────────────────────────────────────────────────

def train(feature_rows: list) -> dict:
    lang_dicts = [r.get("languages", {}) for r in feature_rows if r.get("languages")]

    if len(lang_dicts) < N_CLUSTERS:
        raise ValueError("Not enough users with language data.")

    vocab  = _build_vocab(lang_dicts)
    X_raw  = _vectorize_batch(lang_dicts, vocab)
    X      = normalize(X_raw, norm="l2")

    model  = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20, max_iter=500)
    labels = model.fit_predict(X)

    sil = silhouette_score(X, labels)
    print(f"  [Skill] Silhouette Score : {sil:.3f}")

    label_map = {
        i: _interpret(model.cluster_centers_[i], vocab)
        for i in range(N_CLUSTERS)
    }
    print(f"  [Skill] Cluster map      : {label_map}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": model, "vocab": vocab, "label_map": label_map}, MODEL_PATH)

    return {"metrics": {"silhouette": float(sil)}}


# ── Inference ─────────────────────────────────────────────────────────────────

def predict(features: dict) -> dict:
    artifact  = joblib.load(MODEL_PATH)
    model     = artifact["model"]
    vocab     = artifact["vocab"]
    label_map = artifact["label_map"]

    lang_dict    = features.get("languages", {})
    top_language = max(lang_dict, key=lang_dict.get) if lang_dict else "General Developer"

    if not lang_dict:
        return {"skill_cluster": DEFAULT_LABEL, "top_language": top_language}

    vec = np.array([[lang_dict.get(l, 0.0) for l in vocab]], dtype=np.float64)
    vec = normalize(vec, norm="l2")
    cid = int(model.predict(vec)[0])

    return {
        "skill_cluster": label_map.get(cid, DEFAULT_LABEL),
        "top_language":  top_language,
    }
