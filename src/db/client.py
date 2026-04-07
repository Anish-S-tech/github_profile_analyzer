"""
client.py — Supabase Client

Loads credentials from .env and returns a singleton Supabase client.
All other db modules import from here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_client = None


def get_client():
    """
    Returns the Supabase client singleton.
    Returns None if credentials are not configured — DB features
    will be silently skipped so the app still works without Supabase.
    """
    global _client

    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    if "your-project-id" in SUPABASE_URL:
        return None

    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except Exception:
        return None


def is_configured() -> bool:
    return get_client() is not None
