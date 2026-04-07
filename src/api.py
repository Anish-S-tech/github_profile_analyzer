"""
api.py — FastAPI Backend

Serves the React frontend with:
  POST /analyze   — full pipeline (Phase 1 + 2 + 3 + 4)
  GET  /health    — system health check
  GET  /status    — LLM status

Usage:
    uvicorn src.api:app --reload --port 8000
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.inference.pipeline import analyze
from src.llm.llm_engine     import check_ollama
from src.db                 import is_configured, get_analysis_history

app = FastAPI(title="GitHub Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    username: str
    use_llm:  bool = True


@app.post("/analyze")
async def analyze_user(req: AnalyzeRequest):
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    result = analyze(username, use_cache=True, llm=req.use_llm)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@app.get("/health")
async def health():
    return {"status": "ok", "service": "GitHub Intelligence API"}


@app.get("/status")
async def status():
    ollama = check_ollama()
    return {
        "api":      "ok",
        "ollama":   ollama,
        "database": is_configured(),
    }


@app.get("/history/{username}")
async def history(username: str, limit: int = 10):
    rows = get_analysis_history(username, limit=limit)
    return {"username": username, "history": rows}
