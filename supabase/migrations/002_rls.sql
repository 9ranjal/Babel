alter table public.documents enable row level security;
alter table public.clauses enable row level security;
alter table public.analyses enable row level security;

create policy "doc_owner_select" on public.documents for select using ( user_id = auth.uid() );
create policy "doc_owner_modify" on public.documents for update using ( user_id = auth.uid() ) with check ( user_id = auth.uid() );
create policy "doc_owner_insert" on public.documents for insert with check ( user_id = auth.uid() );
create policy "doc_owner_delete" on public.documents for delete using ( user_id = auth.uid() );

create policy "clause_owner_select" on public.clauses for select using (
  exists (select 1 from public.documents d where d.id = clauses.document_id and d.user_id = auth.uid())
);
create policy "clause_owner_modify" on public.clauses for update using (
  exists (select 1 from public.documents d where d.id = clauses.document_id and d.user_id = auth.uid())
) with check (
  exists (select 1 from public.documents d where d.id = clauses.document_id and d.user_id = auth.uid())
);
create policy "clause_owner_insert" on public.clauses for insert with check (
  exists (select 1 from public.documents d where d.id = clauses.document_id and d.user_id = auth.uid())
);
create policy "clause_owner_delete" on public.clauses for delete using (
  exists (select 1 from public.documents d where d.id = clauses.document_id and d.user_id = auth.uid())
);

create policy "analysis_owner_select" on public.analyses for select using (
  exists (select 1 from public.documents d where d.id = analyses.document_id and d.user_id = auth.uid())
);
create policy "analysis_owner_modify" on public.analyses for update using (
  exists (select 1 from public.documents d where d.id = analyses.document_id and d.user_id = auth.uid())
) with check (
  exists (select 1 from public.documents d where d.id = analyses.document_id and d.user_id = auth.uid())
);
create policy "analysis_owner_insert" on public.analyses for insert with check (
  exists (select 1 from public.documents d where d.id = analyses.document_id and d.user_id = auth.uid())
);
create policy "analysis_owner_delete" on public.analyses for delete using (
  exists (select 1 from public.documents d where d.id = analyses.document_id and d.user_id = auth.uid())
);


