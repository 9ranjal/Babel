# Supabase Database Setup Guide

## 📋 Overview

This directory contains SQL migrations for the Babel AI database schema.

## 🚀 Quick Start - Running Migrations

### **Step 1: Access Supabase SQL Editor**

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Select your project: **mbumjcbfycaxapxqxirg**
3. Click on **SQL Editor** in the left sidebar

### **Step 2: Run Initial Schema Migration**

1. Click **New Query** button
2. Copy the contents of `migrations/001_initial_schema.sql`
3. Paste into the SQL editor
4. Click **Run** (or press Cmd/Ctrl + Enter)
5. Wait for success confirmation (should see "Success. No rows returned")

**What this creates:**
- ✅ 9 core tables (users, personas, sessions, terms, etc.)
- ✅ Row Level Security (RLS) policies for data isolation
- ✅ Indexes for query performance
- ✅ Helper functions and triggers

### **Step 3: Run Seed Data Migration**

1. Click **New Query** again
2. Copy the contents of `migrations/002_seed_data.sql`
3. Paste into the SQL editor
4. Click **Run**
5. Check the output - should see:
   - "Clause library entries: 8"
   - "Market benchmark entries: 24"

**What this creates:**
- ✅ 8 standard term sheet clauses (vesting, valuation cap, etc.)
- ✅ 24 market benchmark data points across regions and stages

### **Step 4: Verify Setup**

Run this verification query in the SQL editor:

```sql
-- Check table counts
SELECT 
  'clause_library' as table_name, 
  COUNT(*) as row_count 
FROM public.clause_library
UNION ALL
SELECT 
  'market_benchmarks' as table_name, 
  COUNT(*) as row_count 
FROM public.market_benchmarks
UNION ALL
SELECT 
  'personas' as table_name, 
  COUNT(*) as row_count 
FROM public.personas;
```

**Expected output:**
- clause_library: 8 rows
- market_benchmarks: 24 rows  
- personas: 0 rows (empty initially)

## 📊 Database Schema

### Core Tables

| Table | Purpose | RLS |
|-------|---------|-----|
| `users` | User accounts (extends Supabase auth) | ✅ |
| `personas` | Company/investor profiles with computed leverage | ✅ |
| `clause_library` | Term sheet clause templates | ✅ (read-only) |
| `market_benchmarks` | Industry benchmark data | ✅ (read-only) |
| `negotiation_sessions` | Active negotiation instances | ✅ |
| `session_terms` | Negotiated clause values per session | ✅ |
| `negotiation_rounds` | Round-by-round negotiation history | ✅ |
| `documents` | Generated term sheet documents | ✅ |
| `orgs` | Organizations (future team features) | ✅ |
| `memberships` | Org membership mappings | ✅ |

### Security Features

**Row Level Security (RLS)** is enabled on all tables:
- Users can only see their own data
- Clause library and market benchmarks are globally readable
- Session data is isolated by owner
- All policies verified in migration scripts

## 🔍 Useful Queries

### View all clause types
```sql
SELECT clause_key, description 
FROM public.clause_library 
ORDER BY clause_key;
```

### Check market data for a specific clause
```sql
SELECT * 
FROM public.market_benchmarks 
WHERE clause_key = 'vesting' 
  AND region = 'US' 
ORDER BY stage;
```

### View RLS policies
```sql
SELECT tablename, policyname, roles, qual 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

## 🛠️ Troubleshooting

### Migration fails with "permission denied"
- Make sure you're using the SQL Editor in your Supabase dashboard
- Verify you're logged in as the project owner

### RLS policies blocking queries
- RLS is working correctly! Use authenticated requests
- For testing, you can temporarily disable RLS:
  ```sql
  ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
  ```
  (Re-enable before production!)

### Tables already exist
If you need to reset:
```sql
-- DANGER: This drops all data!
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

## 📝 Next Steps

After successful migration:
1. ✅ Verify table creation
2. ✅ Test RLS policies with test users
3. ✅ Start backend development (Phase 2)
4. ✅ Wire up frontend (Phase 3)

## 📚 References

- [Supabase SQL Editor Docs](https://supabase.com/docs/guides/database/sql-editor)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)

