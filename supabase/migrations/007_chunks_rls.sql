alter table public.chunks enable row level security;

-- Mirror documents ownership (owner can select/modify chunks of their documents)
create policy if not exists chunks_owner_select on public.chunks
for select using (
  exists (
    select 1 from public.documents d
    where d.id = public.chunks.document_id and d.user_id = auth.uid()
  )
);

create policy if not exists chunks_owner_modify on public.chunks
for all using (
  exists (
    select 1 from public.documents d
    where d.id = public.chunks.document_id and d.user_id = auth.uid()
  )
);


