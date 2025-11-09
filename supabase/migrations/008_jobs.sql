create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  type text not null,
  document_id uuid null,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'queued',           -- queued|working|done|failed
  attempts int not null default 0,
  idempotency_key text unique,
  last_error text,
  failed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_jobs_type_status on public.jobs(type, status);


