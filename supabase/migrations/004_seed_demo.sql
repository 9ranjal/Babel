with u as (
  select '00000000-0000-0000-0000-000000000001'::uuid as demo_user
)
insert into public.documents (user_id, filename, mime, blob_path, text_plain, pages_json, graph_json)
select u.demo_user, 'demo_term_sheet.pdf', 'application/pdf', 'documents/00000000-0000-0000-0000-000000000001/demo-demo.pdf',
       null, null, null from u
on conflict do nothing;


