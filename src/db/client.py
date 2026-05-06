"""
client.py — Supabase Client

Two clients:
  - anon client  : used for auth operations (sign_up, sign_in, get_user)
  - service client: uses service_role key to bypass RLS for DB writes
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY         = os.getenv("SUPABASE_KEY", "")          # anon key
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # service_role key

_anon_client    = None
_service_client = None


def _is_placeholder(url: str) -> bool:
    return not url or "your-project-id" in url


def get_client():
    """Anon client — used for Supabase Auth operations."""
    global _anon_client
    if _anon_client is not None:
        return _anon_client
    if _is_placeholder(SUPABASE_URL) or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        _anon_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _anon_client
    except Exception:
        return None


def get_service_client():
    """Service-role client — bypasses RLS for backend DB writes."""
    global _service_client
    if _service_client is not None:
        return _service_client
    if _is_placeholder(SUPABASE_URL):
        return None
    # Fall back to anon key if service key not set (limited write access)
    key = SUPABASE_SERVICE_KEY or SUPABASE_KEY
    if not key:
        return None
    try:
        from supabase import create_client
        _service_client = create_client(SUPABASE_URL, key)
        return _service_client
    except Exception:
        return None


def is_configured() -> bool:
    return get_client() is not None
