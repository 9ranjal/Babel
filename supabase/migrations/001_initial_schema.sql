-- ============================================================================
-- Babel AI - Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Description: Creates all core tables for persona-driven negotiation system
-- ============================================================================

-- ============================================================================
-- 1. USERS & AUTHENTICATION
-- ============================================================================

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
  user_id UUID PRIMARY KEY DEFAULT auth.uid(),
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_self_select" ON public.users
  FOR SELECT USING (auth.uid() = user_id);

-- ============================================================================
-- 2. ORGANIZATIONS & MEMBERSHIPS (Optional - for future team features)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.orgs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  owner UUID REFERENCES public.users(user_id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.orgs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "orgs_owner_all" ON public.orgs
  USING (auth.uid() = owner);

CREATE TABLE IF NOT EXISTS public.memberships (
  org_id UUID REFERENCES public.orgs(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.users(user_id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('owner','admin','member')) DEFAULT 'member',
  PRIMARY KEY (org_id, user_id)
);

ALTER TABLE public.memberships ENABLE ROW LEVEL SECURITY;

CREATE POLICY "memberships_member_select" ON public.memberships
  FOR SELECT USING (auth.uid() = user_id);

-- ============================================================================
-- 3. PERSONAS (Company & Investor Profiles)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.personas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user UUID REFERENCES public.users(user_id),
  kind TEXT CHECK (kind IN ('company','investor')) NOT NULL,
  attrs JSONB NOT NULL,                -- raw inputs from Q&A
  leverage_score DOUBLE PRECISION,     -- computed leverage λ
  weights JSONB,                       -- per-clause importance weights
  batna JSONB,                         -- best alternative clause defaults
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.personas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "personas_owner_all" ON public.personas
  USING (auth.uid() = owner_user)
  WITH CHECK (auth.uid() = owner_user);

-- Index for faster persona lookups
CREATE INDEX IF NOT EXISTS idx_personas_owner ON public.personas(owner_user);
CREATE INDEX IF NOT EXISTS idx_personas_kind ON public.personas(kind);

-- ============================================================================
-- 4. CLAUSE LIBRARY (Term Sheet Clause Templates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.clause_library (
  clause_key TEXT PRIMARY KEY,
  param_schema JSONB NOT NULL,         -- parameter definitions
  constraints JSONB NOT NULL,          -- bounds, non-negotiable flags
  templates JSONB NOT NULL,            -- markdown/docx snippets
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.clause_library ENABLE ROW LEVEL SECURITY;

-- Everyone can read clause library
CREATE POLICY "clause_library_read_all" ON public.clause_library
  FOR SELECT USING (true);

-- ============================================================================
-- 5. MARKET BENCHMARKS (Industry Data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.market_benchmarks (
  id BIGSERIAL PRIMARY KEY,
  clause_key TEXT REFERENCES public.clause_library(clause_key) ON DELETE CASCADE,
  stage TEXT,                          -- seed, series-a, etc.
  region TEXT,                         -- US, IN, EU, etc.
  p25 NUMERIC,                         -- 25th percentile
  p50 NUMERIC,                         -- median
  p75 NUMERIC,                         -- 75th percentile
  asof_date DATE,                      -- data snapshot date
  source TEXT,                         -- data source reference
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.market_benchmarks ENABLE ROW LEVEL SECURITY;

-- Everyone can read market data
CREATE POLICY "market_benchmarks_read_all" ON public.market_benchmarks
  FOR SELECT USING (true);

-- Index for faster market data queries
CREATE INDEX IF NOT EXISTS idx_market_clause ON public.market_benchmarks(clause_key);
CREATE INDEX IF NOT EXISTS idx_market_stage_region ON public.market_benchmarks(stage, region);

-- ============================================================================
-- 6. NEGOTIATION SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.negotiation_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user UUID REFERENCES public.users(user_id),
  company_persona UUID REFERENCES public.personas(id),
  investor_persona UUID REFERENCES public.personas(id),
  regime TEXT,                         -- legal regime (US, IN, etc.)
  status TEXT CHECK (status IN ('draft','negotiating','final')) DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.negotiation_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sessions_owner_all" ON public.negotiation_sessions
  USING (auth.uid() = owner_user)
  WITH CHECK (auth.uid() = owner_user);

-- Index for faster session queries
CREATE INDEX IF NOT EXISTS idx_sessions_owner ON public.negotiation_sessions(owner_user);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON public.negotiation_sessions(status);

-- ============================================================================
-- 7. SESSION TERMS (Negotiated Clause Values)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.session_terms (
  session_id UUID REFERENCES public.negotiation_sessions(id) ON DELETE CASCADE,
  clause_key TEXT REFERENCES public.clause_library(clause_key),
  value JSONB NOT NULL,                -- actual clause values
  source TEXT CHECK (source IN ('rule','persona','copilot')) DEFAULT 'rule',
  confidence DOUBLE PRECISION,         -- AI confidence score
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (session_id, clause_key)
);

ALTER TABLE public.session_terms ENABLE ROW LEVEL SECURITY;

CREATE POLICY "session_terms_owner_all" ON public.session_terms
  USING (
    EXISTS (
      SELECT 1 FROM public.negotiation_sessions s
      WHERE s.id = session_terms.session_id AND s.owner_user = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.negotiation_sessions s
      WHERE s.id = session_terms.session_id AND s.owner_user = auth.uid()
    )
  );

-- ============================================================================
-- 8. NEGOTIATION ROUNDS (Round-by-round history)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.negotiation_rounds (
  session_id UUID REFERENCES public.negotiation_sessions(id) ON DELETE CASCADE,
  round_no INT,
  company_proposal JSONB,              -- company's proposed values
  investor_proposal JSONB,             -- investor's proposed values
  mediator_choice JSONB,               -- AI mediator's chosen values
  utilities JSONB,                     -- utility scores for both parties
  rationale_md TEXT,                   -- markdown explanation
  decided BOOLEAN DEFAULT false,       -- whether this round was accepted
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (session_id, round_no)
);

ALTER TABLE public.negotiation_rounds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rounds_owner_all" ON public.negotiation_rounds
  USING (
    EXISTS (
      SELECT 1 FROM public.negotiation_sessions s
      WHERE s.id = negotiation_rounds.session_id AND s.owner_user = auth.uid()
    )
  );

-- ============================================================================
-- 9. DOCUMENTS (Generated Term Sheets)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES public.negotiation_sessions(id) ON DELETE CASCADE,
  doc_type TEXT CHECK (doc_type IN ('termsheet')) DEFAULT 'termsheet',
  version INT DEFAULT 1,
  doc_md TEXT,                         -- markdown content
  citations JSONB,                     -- source citations
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "documents_owner_all" ON public.documents
  USING (
    EXISTS (
      SELECT 1 FROM public.negotiation_sessions s
      WHERE s.id = documents.session_id AND s.owner_user = auth.uid()
    )
  );

-- Index for faster document queries
CREATE INDEX IF NOT EXISTS idx_documents_session ON public.documents(session_id);

-- ============================================================================
-- 10. HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at columns
CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON public.personas
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON public.negotiation_sessions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_terms_updated_at BEFORE UPDATE ON public.session_terms
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Run seed data (002_seed_data.sql)
-- 2. Test RLS policies with different users
-- 3. Verify all tables and indexes are created
-- ============================================================================

