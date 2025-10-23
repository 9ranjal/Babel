-- ============================================================================
-- MVP RLS Fix - Allow service role to bypass all restrictions
-- ============================================================================

-- Drop existing restrictive policies
DROP POLICY IF EXISTS "transactions_owner_all" ON public.transactions;
DROP POLICY IF EXISTS "tx_members_read_member" ON public.transaction_members;
DROP POLICY IF EXISTS "tx_members_write_owner" ON public.transaction_members;
DROP POLICY IF EXISTS "tx_personas_member_read" ON public.transaction_personas;
DROP POLICY IF EXISTS "tx_personas_member_write" ON public.transaction_personas;
DROP POLICY IF EXISTS "negotiation_sessions_member_all" ON public.negotiation_sessions;

-- Create service role bypass policies
CREATE POLICY "transactions_service_bypass" ON public.transactions
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "tx_members_service_bypass" ON public.transaction_members
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "tx_personas_service_bypass" ON public.transaction_personas
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "sessions_service_bypass" ON public.negotiation_sessions
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Also allow the test user for manual testing
CREATE POLICY "transactions_test_user" ON public.transactions
  FOR ALL USING (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid);

CREATE POLICY "tx_members_test_user" ON public.transaction_members
  FOR ALL USING (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid);

CREATE POLICY "tx_personas_test_user" ON public.transaction_personas
  FOR ALL USING (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid);

CREATE POLICY "sessions_test_user" ON public.negotiation_sessions
  FOR ALL USING (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid)
  WITH CHECK (auth.uid() = '00000000-0000-0000-0000-000000000000'::uuid);
