-- precept memory store schema (auto-bootstrapped by PostgresMemoryStore).
-- Idempotent: safe to run on every connect.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DO $$ BEGIN
  CREATE TYPE memory_kind AS ENUM (
    'business_context',
    'approved_convention',
    'team_decision',
    'reusable_asset',
    'risk_pattern',
    'workflow'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE memory_scope AS ENUM ('global', 'workspace');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE memory_source AS ENUM ('human', 'ai');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- IMMUTABLE wrapper so the generated column below is allowed.
-- array_to_string is STABLE in core PG, which Postgres rejects in GENERATED ... STORED.
CREATE OR REPLACE FUNCTION precept_tags_to_text(tags TEXT[])
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS $$
  SELECT COALESCE(array_to_string(tags, ' '), '')
$$;

CREATE TABLE IF NOT EXISTS memory_entries (
  id              TEXT PRIMARY KEY,
  kind            memory_kind NOT NULL,
  domain          TEXT NOT NULL,
  title           TEXT NOT NULL,
  body            TEXT NOT NULL,
  tags            TEXT[] NOT NULL DEFAULT '{}',
  approved        BOOLEAN NOT NULL DEFAULT FALSE,
  approved_by     TEXT NOT NULL DEFAULT '',
  repo_path       TEXT NOT NULL DEFAULT '',
  metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  superseded_by   TEXT REFERENCES memory_entries(id) ON DELETE SET NULL,
  superseded_at   TIMESTAMPTZ,
  search_tsv      TSVECTOR GENERATED ALWAYS AS (
                    setweight(to_tsvector('simple'::regconfig, coalesce(title, '')), 'A') ||
                    setweight(to_tsvector('simple'::regconfig, coalesce(body,  '')), 'B') ||
                    setweight(to_tsvector('simple'::regconfig, precept_tags_to_text(tags)), 'C')
                  ) STORED
);

CREATE INDEX IF NOT EXISTS idx_entries_domain     ON memory_entries(domain);
CREATE INDEX IF NOT EXISTS idx_entries_kind       ON memory_entries(kind);
CREATE INDEX IF NOT EXISTS idx_entries_approved   ON memory_entries(approved) WHERE approved;
CREATE INDEX IF NOT EXISTS idx_entries_active     ON memory_entries(domain, kind) WHERE superseded_by IS NULL;
CREATE INDEX IF NOT EXISTS idx_entries_tsv        ON memory_entries USING GIN (search_tsv);
CREATE INDEX IF NOT EXISTS idx_entries_tags       ON memory_entries USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_entries_title_trgm ON memory_entries USING GIN (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_entries_repo_path  ON memory_entries(repo_path);

-- Phase 1 scope/source model: where this entry applies + who created it.
-- scope=workspace + workspace must be non-null; scope=global keeps workspace = ''.
-- source=ai entries also stash repo_name when known (from precept.config).
ALTER TABLE memory_entries ADD COLUMN IF NOT EXISTS scope     memory_scope  NOT NULL DEFAULT 'global';
ALTER TABLE memory_entries ADD COLUMN IF NOT EXISTS source    memory_source NOT NULL DEFAULT 'human';
ALTER TABLE memory_entries ADD COLUMN IF NOT EXISTS workspace TEXT          NOT NULL DEFAULT '';
ALTER TABLE memory_entries ADD COLUMN IF NOT EXISTS repo_name TEXT          NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_entries_scope_workspace ON memory_entries(scope, workspace);
CREATE INDEX IF NOT EXISTS idx_entries_source          ON memory_entries(source);
CREATE INDEX IF NOT EXISTS idx_entries_pending_ai      ON memory_entries(source) WHERE source = 'ai' AND NOT approved;

CREATE TABLE IF NOT EXISTS memory_entry_embeddings (
  entry_id    TEXT PRIMARY KEY REFERENCES memory_entries(id) ON DELETE CASCADE,
  embedding   vector(384) NOT NULL,
  model       TEXT NOT NULL DEFAULT 'all-MiniLM-L6-v2',
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine
  ON memory_entry_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS memory_syntheses (
  domain                    TEXT PRIMARY KEY,
  summary                   TEXT NOT NULL,
  key_themes                TEXT[] NOT NULL DEFAULT '{}',
  open_questions            TEXT[] NOT NULL DEFAULT '{}',
  synthesized_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  synthesized_by            TEXT NOT NULL DEFAULT 'ai',
  entry_count_at_synthesis  INTEGER NOT NULL DEFAULT 0,
  entry_ids                 TEXT[] NOT NULL DEFAULT '{}',
  stale                     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS memory_audit_log (
  id        BIGSERIAL PRIMARY KEY,
  entry_id  TEXT NOT NULL,
  action    TEXT NOT NULL CHECK (action IN ('insert','update','delete','supersede','approve','merge')),
  actor     TEXT NOT NULL DEFAULT 'system',
  at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  diff      JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_audit_entry_at ON memory_audit_log(entry_id, at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action   ON memory_audit_log(action, at DESC);

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at := now(); RETURN NEW; END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_entries_touch ON memory_entries;
CREATE TRIGGER trg_entries_touch BEFORE UPDATE ON memory_entries
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE OR REPLACE FUNCTION mark_synthesis_stale() RETURNS trigger AS $$
DECLARE d TEXT;
BEGIN
  d := COALESCE(NEW.domain, OLD.domain);
  UPDATE memory_syntheses SET stale = TRUE WHERE domain = d;
  RETURN COALESCE(NEW, OLD);
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_entries_stale ON memory_entries;
CREATE TRIGGER trg_entries_stale AFTER INSERT OR UPDATE OR DELETE ON memory_entries
  FOR EACH ROW EXECUTE FUNCTION mark_synthesis_stale();

CREATE OR REPLACE VIEW memory_entries_active AS
  SELECT * FROM memory_entries WHERE superseded_by IS NULL;
