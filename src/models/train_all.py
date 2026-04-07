"""
train_all.py — Phase 2 Training Orchestrator

Loads data/raw/dataset.json built by build_dataset.py,
trains all 4 models, and saves everything to models/.

Usage:
    python -m src.models.train_all
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models import impact_model, skill_model, contribution_model, maturity_model
from src.models.preprocessing import save_scalers

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "raw", "dataset.json"
)


def load_dataset() -> list:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            "dataset.json not found. Run src/data/build_dataset.py first."
        )
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded {len(data)} users from dataset.json")
    return data


def main():
    print("\n" + "="*60)
    print("  PHASE 2 — TRAINING ALL MODELS")
    print("="*60)

    print("\n[1/5] Loading dataset...")
    rows = load_dataset()

    if len(rows) < 30:
        print("ERROR: Need at least 30 users to train.")
        sys.exit(1)

    scalers = {}

    print("\n[2/5] Training Impact Model...")
    result = impact_model.train(rows)
    scalers["impact"] = result["scaler"]

    print("\n[3/5] Training Skill Model...")
    skill_model.train(rows)

    print("\n[4/5] Training Contribution Model...")
    result = contribution_model.train(rows)
    scalers["contribution"] = result["scaler"]

    print("\n[4/5] Training Maturity Model...")
    result = maturity_model.train(rows)
    scalers["maturity"] = result["scaler"]

    print("\n[5/5] Saving scalers...")
    save_scalers(scalers)

    # Summary
    print("\n" + "="*60)
    print("  All models trained successfully.")
    print()
    models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
    for fname in sorted(os.listdir(models_dir)):
        if fname.endswith(".pkl"):
            size = os.path.getsize(os.path.join(models_dir, fname)) // 1024
            print(f"    {fname:35s} {size:>6} KB")
    print("="*60)


if __name__ == "__main__":
    main()
