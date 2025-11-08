<!-- a64eb7cb-770c-420a-9dcf-137ac048d9b9 4fd9c0e2-b0e6-4c6e-84cb-47931ed462bd -->
# MVP Termsheet Copilot (Dev-Only, No Auth)

### Scope

- End-to-end demo: upload → parse → extract → graph → analyze → redraft diff.
- Backend FastAPI (`backend/api`), Frontend Vite React (`frontend`).
- Supabase (Postgres + Storage) accessed ONLY by backend (service role). FE never touches Supabase.
- Dev-only: single `DEMO_USER_ID` read from env; all routes scope reads/writes to it.
- Viewer is HTML text (server-parsed) with span IDs; optional PDF thumbnails for orientation.

---

## Repo layout

- Keep existing structure; add `packages/` for shared TS libs and backend counterparts under `backend/api/services/`.
```
/packages
  /schema/index.ts
  /llm/{client.ts, schemas.ts, prompts/batna.ts}
  /extractors/regex.ts
  /batna/{config.ts, engine.ts, seed/bands.json}
  /graph/cytoscape.ts
  /diff/redline.ts
```


---

## Supabase migrations

Place in `supabase/migrations`. Use 001–004 for demo project.

### 001_init.sql

```sql
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
```

### 002_rls.sql

```sql
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
```

### 003_storage.sql

```sql
-- Private bucket for term sheet files
insert into storage.buckets (id, name, public) values ('documents','documents', false)
  on conflict (id) do nothing;

-- Path convention (enforced by code): documents/{user_id}/{document_id}/{filename}
-- Service role bypasses RLS; FE will always use backend-signed URLs.
```

### 004_seed_demo.sql (optional)

```sql
with u as (
  select '00000000-0000-0000-0000-000000000001'::uuid as demo_user
)
insert into public.documents (user_id, filename, mime, blob_path, text_plain, pages_json, graph_json)
select u.demo_user, 'demo_term_sheet.pdf', 'application/pdf', 'documents/00000000-0000-0000-0000-000000000001/demo-demo.pdf',
       null, null, null from u
on conflict do nothing;
```

Notes:

- Service role bypasses RLS automatically. FE never hits Supabase directly.

---

## Backend (FastAPI)

New/updated modules under `backend/api`:

- `services/supabase_client.py`: Postgres engine + Storage helpers (signed URL, upload).
- `core/settings.py`: load `DEMO_USER_ID`, Supabase URLs/keys; expose `get_demo_user_id()`.
- `models/tables.py`: SQLAlchemy models.
- `models/schemas.py`: Pydantic responses (include `pages_json` which holds parsed HTML pages with span IDs and offsets).
- `services/parse_pdf.py`: extract text + paragraph blocks; generate lightweight HTML per page with `<span id="clause-<n>">` anchors (heuristics by newline/regex hints). Also (optional) generate 1–3 thumbnails (PNG) for orientation.
- `services/parse_docx.py`: plaintext + HTML via `mammoth` with span IDs.
- `services/extract_regex.py`: regex hints → candidate snippets.
- `services/extract_llm.py`: normalize to ontology; temperature 0.
- `services/band_map.py`: load bands JSON; Python `pick_band`.
- `services/build_graph.py`: nodes/edges from clauses; include cross-links.
- `services/analyze.py`: UPSERT cache by (document_id, clause_id); return existing if present.
- `services/redraft.py`: generate and persist `redraft_text`.
- `routes/upload.py`, `routes/documents.py`, `routes/clauses.py`: always scope by `DEMO_USER_ID`.

Route guarantees:

- `/clauses/:id/analyze`: idempotent by unique index + `INSERT ... ON CONFLICT (document_id, clause_id) DO UPDATE SET ...`.
- All queries filter with `WHERE documents.user_id = :demo_user_id`.

Env (backend only):

```
SUPABASE_DB_URL=postgres://...
SUPABASE_URL=https://YOUR.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
DEMO_USER_ID=00000000-0000-0000-0000-000000000001
```

Supabase keys live ONLY on backend.

---

## Frontend (Vite React)

Components under `frontend/src`:

- `layouts/MainLayout.tsx`: two-pane (Copilot ←→ Viewer) with top tabs: Document | Graph.
- `components/SplitPane.tsx`: simple grid-based splitter.
- `components/Viewer/DocumentViewer.tsx`: HTML viewer (server-parsed pages). Accepts `htmlPages`, highlights via span IDs, and diff overlay (diff-match-patch) for redrafts. Optional thumbnail strip for orientation only.
- `components/Viewer/GraphViewer.tsx`: Cytoscape; click node → select clause and trigger analyze.
- `components/Copilot/Thread.tsx`: left pane messages.
- `components/Copilot/BatnaCard.tsx`: shows band, leverage, risks, recommendation, trades, Redraft chip.
- `lib/api.ts`: fetchers to backend only.
- `lib/store.ts`: Zustand slices for doc, selection, analyses.
- `lib/highlight.ts`: map clauseId → spanId.

FE env:

```
VITE_API_URL=http://localhost:5001
```

(No Supabase env on FE in this cut-line.)

---

## Shared packages (TS)

- `/packages/batna/config.ts`: `DEFAULT_LEVERAGE`.
- `/packages/batna/seed/bands.json`: seed `exclusivity` (extend later).
- `/packages/batna/engine.ts`: `pickBand` implementation.
- `/packages/llm/schemas.ts`, `/packages/llm/prompts/batna.ts`: schemas/prompts.
- `/packages/diff/redline.ts`: wrappers over diff-match-patch for side-by-side markup.

---

## Replace legacy Supabase usages

- Remove any FE Supabase client usage; FE calls backend only.
- Replace legacy backend helpers with `services/supabase_client.py`.

---

## Acceptance tests

- RLS: user A cannot read user B rows when using anon JWT; service role sees both.
- Analyze idempotency: calling `/clauses/:id/analyze` twice returns same `analysis.id` and content (no duplicates due to unique index).

---

## Dev commands

- `make dev`: run FastAPI (uvicorn) + Vite.
- `make seed`: ensure bands are available to backend (read from file path).
- `make demo`: seed a demo document and precomputed extraction if needed.

### To-dos

- [ ] Add 001_init.sql, 002_rls.sql, 003_storage.sql, 004_seed_demo.sql to supabase/migrations
- [ ] Create supabase_client.py for Postgres and Storage signed URLs
- [ ] Add SQLAlchemy models and Pydantic schemas for documents/clauses/analyses
- [ ] Implement parse_pdf.py and parse_docx.py (text + pages_json + HTML snapshot)
- [ ] Implement planner, regex, LLM refine, band_map, build_graph services
- [ ] Implement upload, documents, clauses routes with DEMO_USER_ID
- [ ] Add bands.json, config.ts, engine.ts
- [ ] Add SplitPane, DocumentViewer, GraphViewer, Thread, BatnaCard
- [ ] Add api.ts fetchers and Zustand store
- [ ] Write RLS acceptance tests for Supabase project