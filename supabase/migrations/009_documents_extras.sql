alter table public.documents add column if not exists checksum text;
create index if not exists idx_documents_user_checksum on public.documents(user_id, checksum);
alter table public.documents add column if not exists status text;  -- uploaded|parsed|chunked|extracted|graphed|analyzed|failed


