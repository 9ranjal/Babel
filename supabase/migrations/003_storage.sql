-- Private bucket for term sheet files
insert into storage.buckets (id, name, public) values ('documents','documents', false)
  on conflict (id) do nothing;

-- Path convention (enforced by code): documents/{user_id}/{document_id}/{filename}
-- Service role bypasses RLS; FE will always use backend-signed URLs.


