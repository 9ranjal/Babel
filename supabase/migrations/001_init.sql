create extension if not exists pgcrypto; -- gen_random_uuid()

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  filename text not null,
  mime text,
  blob_path text not null,
  pages_json jsonb,        -- includes parsed HTML pages and offsets
  text_plain text,
  graph_json jsonb,
  leverage_json jsonb not null default '{"investor":0.6,"founder":0.4}',
  created_at timestamptz not null default now()
);
create index if not exists idx_documents_user on public.documents(user_id);

create table if not exists public.clauses (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  clause_key text,
  title text,
  text text,
  start_idx int,
  end_idx int,
  page_hint int,
  band_key text,
  score numeric,
  json_meta jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_clauses_doc on public.clauses(document_id);
create index if not exists idx_clauses_key on public.clauses(clause_key);

create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  clause_id uuid not null references public.clauses(id) on delete cascade,
  band_name text,
  band_score numeric,
  inputs_json jsonb,
  analysis_json jsonb,
  redraft_text text,
  created_at timestamptz not null default now()
);
create index if not exists idx_analyses_doc on public.analyses(document_id);
create index if not exists idx_analyses_clause on public.analyses(clause_id);
-- Idempotency for /clauses/:id/analyze
create unique index if not exists uniq_analyses_doc_clause on public.analyses(document_id, clause_id);


