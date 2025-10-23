-- ============================================================================
-- Transactions model (root node)
-- ============================================================================

-- 1) TRANSACTIONS
CREATE TABLE IF NOT EXISTS public.transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user UUID REFERENCES public.users(user_id) ON DELETE CASCADE,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_owner ON public.transactions(owner_user);

-- RLS
CREATE POLICY "transactions_owner_all" ON public.transactions
  USING (auth.uid() = owner_user)
  WITH CHECK (auth.uid() = owner_user);

-- 2) TRANSACTION MEMBERS
CREATE TABLE IF NOT EXISTS public.transaction_members (
  transaction_id UUID REFERENCES public.transactions(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.users(user_id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('owner','editor','viewer')) DEFAULT 'viewer',
  added_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (transaction_id, user_id)
);

ALTER TABLE public.transaction_members ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_tx_members_tx ON public.transaction_members(transaction_id);

-- RLS: member can select; owner can manage
CREATE POLICY "tx_members_read_member" ON public.transaction_members
  FOR SELECT USING (
    auth.uid() = user_id OR
    EXISTS (SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid())
  );

CREATE POLICY "tx_members_write_owner" ON public.transaction_members
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid())
  );

-- 3) TRANSACTION PERSONAS (link personas into a transaction)
CREATE TABLE IF NOT EXISTS public.transaction_personas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id UUID REFERENCES public.transactions(id) ON DELETE CASCADE,
  kind TEXT CHECK (kind IN ('company','investor')) NOT NULL,
  label TEXT,
  persona_id UUID REFERENCES public.personas(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.transaction_personas ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_tx_personas_tx_kind ON public.transaction_personas(transaction_id, kind);

-- RLS: members of transaction can read/write
CREATE POLICY "tx_personas_member_read" ON public.transaction_personas
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.transaction_members m
      WHERE m.transaction_id = transaction_id AND m.user_id = auth.uid()
    ) OR EXISTS (
      SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid()
    )
  );

CREATE POLICY "tx_personas_member_write" ON public.transaction_personas
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.transaction_members m
      WHERE m.transaction_id = transaction_id AND m.user_id = auth.uid()
    ) OR EXISTS (
      SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.transaction_members m
      WHERE m.transaction_id = transaction_id AND m.user_id = auth.uid()
    ) OR EXISTS (
      SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid()
    )
  );

-- 4) NEGOTIATION SESSIONS: add transaction_id (nullable for backfill)
ALTER TABLE public.negotiation_sessions ADD COLUMN IF NOT EXISTS transaction_id UUID REFERENCES public.transactions(id);
CREATE INDEX IF NOT EXISTS idx_sessions_tx ON public.negotiation_sessions(transaction_id);

-- RLS: members can read/write sessions
DROP POLICY IF EXISTS negotiation_sessions_rls ON public.negotiation_sessions;
CREATE POLICY "negotiation_sessions_member_all" ON public.negotiation_sessions
  USING (
    transaction_id IS NULL OR
    EXISTS (
      SELECT 1 FROM public.transaction_members m
      WHERE m.transaction_id = transaction_id AND m.user_id = auth.uid()
    ) OR EXISTS (
      SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid()
    )
  ) WITH CHECK (
    transaction_id IS NULL OR
    EXISTS (
      SELECT 1 FROM public.transaction_members m
      WHERE m.transaction_id = transaction_id AND m.user_id = auth.uid()
    ) OR EXISTS (
      SELECT 1 FROM public.transactions t WHERE t.id = transaction_id AND t.owner_user = auth.uid()
    )
  );

-- Note: After backfill, enforce NOT NULL on negotiation_sessions.transaction_id.
-- This migration is additive and safe to run multiple times.
