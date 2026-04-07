# GitHub Profile Analyzer

> ML-powered GitHub developer profile analyzer with AI-generated insights.

Enter any GitHub username and get an instant analysis of impact, skills,
contribution style, maturity score, and AI career advice — powered by
local LLMs via Ollama.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev)

---

## Features

- **Impact Score** — ML-predicted influence level (0–100) with log-scaled fair scoring
- **Skill Detection** — Language-based developer type classification (AI/Data, Web, Systems, Backend, Mobile)
- **Contribution Style** — How the developer builds and ships (Consistent, Fast Builder, Low Activity)
- **Maturity Score** — Project depth and consistency (0–100)
- **AI Insights** — Summary, strengths, weaknesses, suggestions, and 30-day growth plan via Ollama
- **Database Caching** — Supabase-backed 24h result cache (optional)
- **History Tracking** — Multiple analysis runs stored per user

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Collection | GitHub REST API |
| ML Models | scikit-learn (RandomForest, KMeans) |
| LLM | Ollama (llama3.2 / any local model) |
| Backend API | FastAPI + Uvicorn |
| Frontend | React + Vite + Recharts |
| Database | Supabase (PostgreSQL) — optional |

---

## Model Evaluation

### Impact Model — RandomForest Classifier

| Metric | Value |
|---|---|
| Accuracy | 0.902 |
| ROC-AUC (5-fold CV) | 0.986 ± 0.014 |
| Precision (High Impact) | 0.74 |
| Recall (High Impact) | 0.93 |
| F1 (High Impact) | 0.82 |

- **Label strategy**: Top 25% by followers = High Impact. Followers is held out of features to avoid circular leakage.
- **Features used**: `total_stars`, `total_forks`, `stars_per_repo`, `growth_rate`, `ff_ratio`, `repo_count`, `avg_stars_per_repo`, `avg_forks_per_repo`
- **Scoring**: Log-scaled weighted formula with base score boost for active users → fair 0–100 range

### Skill Model — KMeans Clustering

| Metric | Value |
|---|---|
| Silhouette Score | 0.316 |
| Clusters | 5 |

- **Input**: L2-normalized language distribution vector (top 20 languages)
- **Clusters**: AI/Data Developer, Web Developer, Systems Developer, Backend Developer, Multi-stack Developer

### Contribution Model — KMeans Clustering

| Metric | Value |
|---|---|
| Silhouette Score | 0.254 |
| Clusters | 3 |

- **Input**: `repo_count`, `stars_per_repo`, `growth_rate`, `account_age_days`, `activity_ratio`, `repo_per_year`
- **Clusters**: Consistent Developer, Fast Builder, Low Activity Developer
- **Interpretation**: Clusters ranked by combined growth_rate + repo_per_year + activity_ratio centroid scores

### Maturity Model — RandomForest Regressor

| Metric | Value |
|---|---|
| R² Score | 0.219 |
| MAE | 0.360 |

- **Target**: `log(account_age_days)` — held out from features to avoid leakage
- **Features used**: `total_stars`, `total_forks`, `repo_count`, `stars_per_repo`, `avg_stars_per_repo`, `topic_diversity`
- **Output**: Remapped to 20–100 range for active users (dead profiles stay near 0)

> All models trained on 302 real GitHub users collected via the GitHub Search API across balanced follower ranges (1 to 295,000+ followers).

---

## Project Structure

```
src/
  pipeline/       Phase 1 — GitHub data fetch, clean, feature engineering
  models/         Phase 2 — ML model training and inference
  inference/      Phase 3 — Inference engine and post-processing
  llm/            Phase 4 — Ollama LLM layer
  db/             Database layer (Supabase)
  data/           Dataset builder
  api.py          FastAPI backend

frontend/         React dashboard (Vite + Recharts)

models/           Trained .pkl files (generated, not committed)
data/             Cache and raw dataset (generated, not committed)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Anish-S-tech/github_profile_analyzer.git
cd github_profile_analyzer
```

### 2. Create and activate virtual environment

```bash
python -m venv myenv

# Windows
myenv\Scripts\activate.bat

# macOS / Linux
source myenv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `GITHUB_TOKEN` — [Create a GitHub token](https://github.com/settings/tokens) (no scopes needed for public data)
- `SUPABASE_URL` and `SUPABASE_KEY` — optional, for persistent storage

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Build the Dataset and Train Models

```bash
# Collect real GitHub users via GitHub Search API
python -m src.data.build_dataset

# Train all 4 ML models
python -m src.models.train_all
```

---

## Run the Project

You need 3 terminals:

**Terminal 1 — Ollama (LLM)**
```bash
ollama serve
ollama pull llama3.2
```

**Terminal 2 — Backend**
```bash
myenv\Scripts\activate.bat        # Windows
uvicorn src.api:app --reload --port 8000
```

**Terminal 3 — Frontend**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze` | Full analysis for a username |
| GET | `/health` | API health check |
| GET | `/status` | Ollama + DB status |
| GET | `/history/{username}` | Analysis history for a user |

---

## Database Setup (Optional)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the contents of `src/db/schema.sql`
3. Copy your **Project URL** and **anon key** from Settings → API
4. Add them to `.env`

The app works fully without Supabase — DB errors never break a request.

---

## Score Design

| Score | Range | Level |
|---|---|---|
| Impact | 0–20 | Explorer |
| Impact | 20–40 | Growing |
| Impact | 40–70 | Advanced |
| Impact | 70–100 | High Impact |
| Maturity | 0–25 | Early Stage |
| Maturity | 25–50 | Developing |
| Maturity | 50–75 | Experienced |
| Maturity | 75–100 | Expert |

Impact score formula:
```
score = base(10 if repos > 0) 
      + ml_signal(25) 
      + log_followers(25) 
      + log_stars(25) 
      + log_repos(10) 
      + growth(5)
```

---

