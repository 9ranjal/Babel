-- ============================================================================
-- MVP RLS Bypass for Service Role (Beta/MVP)
-- ============================================================================

-- Allow service role to bypass all RLS restrictions for MVP
-- This is safe for beta/MVP since service role has full database access anyway

-- Transactions: Service role can do everything
CREATE POLICY "transactions_service_role_all" ON public.transactions
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Transaction Members: Service role can do everything  
CREATE POLICY "tx_members_service_role_all" ON public.transaction_members
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Transaction Personas: Service role can do everything
CREATE POLICY "tx_personas_service_role_all" ON public.transaction_personas
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Negotiation Sessions: Service role can do everything
CREATE POLICY "sessions_service_role_all" ON public.negotiation_sessions
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Note: This allows the FastAPI backend (using service role key) to:
-- - Create transactions without user authentication
-- - Link personas to transactions
-- - Create negotiation sessions
-- - Bypass all RLS restrictions for MVP testing

-- For production, replace these with proper user-based RLS policies
