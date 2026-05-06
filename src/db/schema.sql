-- ============================================================
-- DevProfile AI — Database Schema v2
-- Run this in Supabase SQL Editor
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── TABLE: users (GitHub profiles) ───────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    username            TEXT        NOT NULL UNIQUE,
    followers           INTEGER     NOT NULL DEFAULT 0,
    following           INTEGER     NOT NULL DEFAULT 0,
    repo_count          INTEGER     NOT NULL DEFAULT 0,
    total_stars         INTEGER     NOT NULL DEFAULT 0,
    total_forks         INTEGER     NOT NULL DEFAULT 0,
    top_language        TEXT,
    account_created_at  TIMESTAMPTZ,
    last_fetched_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── TABLE: analysis ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    impact_score        FLOAT       NOT NULL DEFAULT 0,
    impact_level        TEXT        NOT NULL DEFAULT 'Explorer',
    impact_probability  FLOAT       NOT NULL DEFAULT 0,
    skill_type          TEXT,
    contribution_type   TEXT,
    maturity_score      FLOAT       NOT NULL DEFAULT 0,
    maturity_level      TEXT        NOT NULL DEFAULT 'Early Stage',
    llm_summary         TEXT,
    llm_strengths       TEXT[]      DEFAULT '{}',
    llm_weaknesses      TEXT[]      DEFAULT '{}',
    llm_suggestions     TEXT[]      DEFAULT '{}',
    llm_growth_plan     TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── TABLE: languages ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS languages (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language    TEXT        NOT NULL,
    percentage  FLOAT       NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── TABLE: search_history (which app user searched whom) ─────
CREATE TABLE IF NOT EXISTS search_history (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_user_id     UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    github_username TEXT        NOT NULL,
    analysis_id     UUID        REFERENCES analysis(id) ON DELETE SET NULL,
    searched_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── INDEXES ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_username           ON users(username);
CREATE INDEX IF NOT EXISTS idx_analysis_user_id         ON analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at      ON analysis(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_languages_user_id        ON languages(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_app_user  ON search_history(app_user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_searched  ON search_history(searched_at DESC);

-- ── ROW LEVEL SECURITY ────────────────────────────────────────
ALTER TABLE users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis        ENABLE ROW LEVEL SECURITY;
ALTER TABLE languages       ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history  ENABLE ROW LEVEL SECURITY;

-- Public read: anyone can read GitHub profiles, analysis, and languages
CREATE POLICY "public_read_users"     ON users     FOR SELECT USING (true);
CREATE POLICY "public_read_analysis"  ON analysis  FOR SELECT USING (true);
CREATE POLICY "public_read_languages" ON languages FOR SELECT USING (true);

-- Service role writes: only the backend (service_role key) can insert/update/delete
CREATE POLICY "service_write_users"
    ON users FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_write_analysis"
    ON analysis FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_write_languages"
    ON languages FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_write_search_history"
    ON search_history FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

-- Users can only read their own search history (when using anon/user token)
CREATE POLICY "own_read_search_history" ON search_history
    FOR SELECT USING (auth.uid() = app_user_id);
