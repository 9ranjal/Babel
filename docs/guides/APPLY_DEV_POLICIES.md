# 🔓 Apply Development Policies

## Issue
Row-level security (RLS) is blocking persona creation because we're using a placeholder user ID for testing.

## Solution
Apply the migration `003_dev_policies.sql` to allow testing without full authentication.

---

## Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase Dashboard: https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new

2. Copy and paste this SQL:

```sql
-- Allow inserts/selects/updates/deletes for testing personas
CREATE POLICY "personas_test_insert" ON public.personas
  FOR INSERT
  WITH CHECK (owner_user = '00000000-0000-0000-0000-000000000000'::uuid);

CREATE POLICY "personas_test_select" ON public.personas
  FOR SELECT
  USING (owner_user = '00000000-0000-0000-0000-000000000000'::uuid);

CREATE POLICY "personas_test_update" ON public.personas
  FOR UPDATE
  USING (owner_user = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (owner_user = '00000000-0000-0000-0000-000000000000'::uuid);

CREATE POLICY "personas_test_delete" ON public.personas
  FOR DELETE
  USING (owner_user = '00000000-0000-0000-0000-000000000000'::uuid);

-- Allow testing for negotiation sessions
CREATE POLICY "sessions_test_all" ON public.negotiation_sessions
  FOR ALL
  USING (owner_user = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (owner_user = '00000000-0000-0000-0000-000000000000'::uuid);
```

3. Click "Run" to execute

4. You should see: "Success. No rows returned"

---

## Option 2: Command Line (if you have psql)

```bash
# Get your database connection string from Supabase dashboard
# Then run:
psql 'YOUR_CONNECTION_STRING' -f supabase/migrations/003_dev_policies.sql
```

---

## Option 3: Temporarily Disable RLS (Quick Test Only)

**⚠️ WARNING: Only for local development!**

```sql
-- In Supabase Dashboard SQL Editor:
ALTER TABLE public.personas DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.negotiation_sessions DISABLE ROW LEVEL SECURITY;

-- Remember to re-enable after testing:
-- ALTER TABLE public.personas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.negotiation_sessions ENABLE ROW LEVEL SECURITY;
```

---

## Verify It Worked

After applying, test the API again:

```bash
curl -X POST http://localhost:8000/api/personas/ \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "company",
    "attrs": {"stage": "seed"},
    "leverage_score": 0.6,
    "weights": {},
    "batna": {}
  }'
```

You should get a successful response with a persona ID!

---

## Note

These policies allow operations when `owner_user` is the placeholder UUID `00000000-0000-0000-0000-000000000000`.

In production, you'll want to:
1. Implement proper authentication
2. Remove these test policies
3. Use real user IDs from auth.uid()

