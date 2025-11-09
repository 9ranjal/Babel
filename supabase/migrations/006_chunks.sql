create table if not exists public.chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  clause_id uuid null references public.clauses(id) on delete set null,
  block_id text not null,
  page int not null,
  kind text not null,
  text text not null,
  meta jsonb not null default '{}'::jsonb,
  embedding vector(1536),
  created_at timestamptz not null default now()
);

create index if not exists idx_chunks_document_id on public.chunks(document_id);
create index if not exists idx_chunks_clause_id on public.chunks(clause_id);

-- pgvector IVF index for cosine search (performance)
create index if not exists idx_chunks_embedding_cosine
  on public.chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);


