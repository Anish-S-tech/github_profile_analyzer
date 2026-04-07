# GitHub Intelligence

ML-powered GitHub developer profile analyzer with AI-generated insights.

Enter any GitHub username and get an instant analysis of impact, skills,
contribution style, maturity score, and AI career advice — powered by
local LLMs via Ollama.

---

## Features

- **Impact Score** — ML-predicted influence level (0–100)
- **Skill Detection** — Language-based developer type classification
- **Contribution Style** — How the developer builds and ships
- **Maturity Score** — Project depth and consistency (0–100)
- **AI Insights** — Summary, strengths, weaknesses, suggestions, and 30-day growth plan via Ollama
- **Database Caching** — Supabase-backed 24h result cache (optional)

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

frontend/         React dashboard (Vite)

models/           Trained .pkl files (generated, not committed)
data/             Cache and raw dataset (generated, not committed)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/Github_Intelligence.git
cd Github_Intelligence
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
# Collect real GitHub users (runs Phase 1 pipeline)
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

## Models

| Model | Type | Purpose |
|---|---|---|
| Impact | RandomForest Classifier | Predicts developer influence |
| Skill | KMeans Clustering | Classifies developer type by language |
| Contribution | KMeans Clustering | Classifies working style |
| Maturity | RandomForest Regressor | Scores project depth |

Models are not committed to the repo. Run `train_all.py` to generate them.
