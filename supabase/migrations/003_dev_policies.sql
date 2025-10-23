-- ============================================================================
-- Development/Testing Policies
-- Migration: 003_dev_policies.sql
-- Description: Add permissive policies for development and testing
-- ============================================================================

-- Allow inserts for testing (when owner_user is the placeholder UUID)
-- This allows API testing without full auth setup
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

-- Similar policies for negotiation sessions
CREATE POLICY "sessions_test_all" ON public.negotiation_sessions
  FOR ALL
  USING (owner_user = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (owner_user = '00000000-0000-0000-0000-000000000000'::uuid);

-- ============================================================================
-- NOTE: Remove these policies in production!
-- These are only for development/testing without full auth
-- ============================================================================

