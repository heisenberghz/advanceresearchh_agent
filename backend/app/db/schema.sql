-- =====================================================================
-- ResearchOps Database Schema (Supabase PostgreSQL)
-- Specification: TECH_SPEC.md Section 25 & PRD.md
-- =====================================================================

-- Enable UUID extension if not already present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. research_runs: Tracks high-level research requests and states
CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    assumptions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

-- 2. research_jobs: Individual sub-tasks dispatched to researchers
CREATE TABLE IF NOT EXISTS research_jobs (
    id TEXT PRIMARY KEY,
    research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    entity TEXT,
    attribute TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, needs_retry, failed
    attempts INTEGER NOT NULL DEFAULT 0,
    result_data JSONB DEFAULT '{}'::jsonb,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. sources: Provenance records for web pages retrieved
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    domain TEXT,
    publisher TEXT,
    published_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. facts: Discrete extracted claims with trust indicators
CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    entity TEXT NOT NULL,
    attribute TEXT NOT NULL,
    value TEXT NOT NULL,
    normalized_value TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unverified', -- verified, uncertain, conflicting, unsupported, missing
    trust_tag TEXT NOT NULL DEFAULT 'RED',                  -- GREEN, YELLOW, RED
    verification_reason TEXT,
    evidence JSONB DEFAULT '[]'::jsonb,
    source_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 5. conflicts: Contradictory evidence across multiple sources
CREATE TABLE IF NOT EXISTS conflicts (
    id TEXT PRIMARY KEY,
    research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unresolved', -- unresolved, explained, resolved
    competing_values JSONB DEFAULT '[]'::jsonb,
    supporting_sources JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 6. research_gaps: Information that could not be verified
CREATE TABLE IF NOT EXISTS research_gaps (
    id TEXT PRIMARY KEY,
    research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    requested_information TEXT NOT NULL,
    reason TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'gap',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 7. reports: Final synthesized research report
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE UNIQUE,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_research_jobs_run ON research_jobs(research_run_id);
CREATE INDEX IF NOT EXISTS idx_sources_run ON sources(research_run_id);
CREATE INDEX IF NOT EXISTS idx_facts_run ON facts(research_run_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_run ON conflicts(research_run_id);
CREATE INDEX IF NOT EXISTS idx_gaps_run ON research_gaps(research_run_id);
