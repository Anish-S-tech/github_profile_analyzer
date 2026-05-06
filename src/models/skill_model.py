"""
skill_model.py - Skill Model (Unsupervised Clustering)

Input  : language distribution dict { "Python": 0.5, "JS": 0.3, ... }
Output : skill_cluster, top_language

Improvements for generalization:
  - Auto-select optimal k (3-7) via silhouette score
  - IDF-weighted language vectors (rare langs get more weight)
  - Larger vocab (top 25 languages)
  - MiniBatchKMeans for stability on varied data
"""

import numpy as np
import joblib
import os
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "skill_model.pkl"
)

VOCAB_SIZE = 25
K_RANGE    = range(3, 8)   # search best k from 3 to 7

LANG_TO_LABEL = {
    "Python":           "AI / Data Developer",
    "Jupyter Notebook": "AI / Data Developer",
    "R":                "AI / Data Developer",
    "JavaScript":       "Web Developer",
    "TypeScript":       "Web Developer",
    "HTML":             "Web Developer",
    "CSS":              "Web Developer",
    "Vue":              "Web Developer",
    "C":                "Systems Developer",
    "C++":              "Systems Developer",
    "Rust":             "Systems Developer",
    "Go":               "Systems Developer",
    "Assembly":         "Systems Developer",
    "Zig":              "Systems Developer",
    "Java":             "Backend Developer",
    "Kotlin":           "Backend Developer",
    "PHP":              "Backend Developer",
    "Ruby":             "Backend Developer",
    "Scala":            "Backend Developer",
    "C#":               "Backend Developer",
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


def _idf_weights(lang_dicts: list, vocab: list) -> np.ndarray:
    """
    Compute IDF weight per vocab term.
    Languages used by fewer developers get higher weight — more discriminative.
    """
    n = len(lang_dicts)
    df = np.array([
        sum(1 for ld in lang_dicts if ld.get(lang, 0) > 0)
        for lang in vocab
    ], dtype=np.float64)
    df = np.maximum(df, 1)
    return np.log((n + 1) / (df + 1)) + 1.0   # smoothed IDF


def _vectorize_batch(lang_dicts: list, vocab: list, idf: np.ndarray) -> np.ndarray:
    X = np.array(
        [[ld.get(lang, 0.0) for lang in vocab] for ld in lang_dicts],
        dtype=np.float64,
    )
    return X * idf   # TF-IDF style weighting


def _interpret(center: np.ndarray, vocab: list) -> str:
    if center.sum() == 0:
        return DEFAULT_LABEL
    top_lang = vocab[int(np.argmax(center))]
    return LANG_TO_LABEL.get(top_lang, DEFAULT_LABEL)


def train(feature_rows: list) -> dict:
    lang_dicts = [r.get("languages", {}) for r in feature_rows if r.get("languages")]

    if len(lang_dicts) < max(K_RANGE):
        raise ValueError("Not enough users with language data.")

    vocab = _build_vocab(lang_dicts)
    idf   = _idf_weights(lang_dicts, vocab)
    X_raw = _vectorize_batch(lang_dicts, vocab, idf)
    X     = normalize(X_raw, norm="l2")

    # Search for best k
    best_k, best_sil, best_model, best_labels = 3, -1, None, None
    for k in K_RANGE:
        m = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=20, max_iter=500)
        lbl = m.fit_predict(X)
        sil = silhouette_score(X, lbl)
        print(f"  [Skill] k={k} silhouette={sil:.3f}")
        if sil > best_sil:
            best_k, best_sil, best_model, best_labels = k, sil, m, lbl

    print(f"  [Skill] Best k={best_k}  Silhouette={best_sil:.3f}")

    label_map = {
        i: _interpret(best_model.cluster_centers_[i], vocab)
        for i in range(best_k)
    }
    print(f"  [Skill] Cluster map: {label_map}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({
        "model":     best_model,
        "vocab":     vocab,
        "idf":       idf,
        "label_map": label_map,
    }, MODEL_PATH)

    return {"metrics": {"silhouette": float(best_sil), "k": best_k}}


def predict(features: dict) -> dict:
    artifact  = joblib.load(MODEL_PATH)
    model     = artifact["model"]
    vocab     = artifact["vocab"]
    idf       = artifact["idf"]
    label_map = artifact["label_map"]

    lang_dict    = features.get("languages", {})
    top_language = max(lang_dict, key=lang_dict.get) if lang_dict else "General Developer"

    if not lang_dict:
        return {"skill_cluster": DEFAULT_LABEL, "top_language": top_language}

    vec = np.array([[lang_dict.get(l, 0.0) for l in vocab]], dtype=np.float64) * idf
    vec = normalize(vec, norm="l2")
    cid = int(model.predict(vec)[0])

    return {
        "skill_cluster": label_map.get(cid, DEFAULT_LABEL),
        "top_language":  top_language,
    }
