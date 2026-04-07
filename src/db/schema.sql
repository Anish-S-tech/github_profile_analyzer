-- ============================================================
-- GitHub Intelligence — Database Schema
-- Run this in Supabase SQL Editor (once)
-- ============================================================

-- ── Extensions ───────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── TABLE: users ─────────────────────────────────────────────
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

    -- Impact
    impact_score        FLOAT       NOT NULL DEFAULT 0,
    impact_level        TEXT        NOT NULL DEFAULT 'Explorer',
    impact_probability  FLOAT       NOT NULL DEFAULT 0,

    -- Skill & Contribution
    skill_type          TEXT,
    contribution_type   TEXT,

    -- Maturity
    maturity_score      FLOAT       NOT NULL DEFAULT 0,
    maturity_level      TEXT        NOT NULL DEFAULT 'Early Stage',

    -- LLM Insights
    llm_summary         TEXT,
    llm_strengths       TEXT[]      DEFAULT '{}',
    llm_weaknesses      TEXT[]      DEFAULT '{}',
    llm_suggestions     TEXT[]      DEFAULT '{}',
    llm_growth_plan     TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── TABLE: languages ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS languages (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language    TEXT    NOT NULL,
    percentage  FLOAT   NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── INDEXES ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_username        ON users(username);
CREATE INDEX IF NOT EXISTS idx_analysis_user_id      ON analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at   ON analysis(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_languages_user_id     ON languages(user_id);

-- ── ROW LEVEL SECURITY ────────────────────────────────────────
ALTER TABLE users     ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis  ENABLE ROW LEVEL SECURITY;
ALTER TABLE languages ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (tighten later with auth)
CREATE POLICY "allow_all_users"     ON users     FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_analysis"  ON analysis  FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_languages" ON languages FOR ALL USING (true) WITH CHECK (true);
