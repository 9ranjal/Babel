-- Create a test transaction for MVP testing
-- Run this in Supabase SQL Editor

INSERT INTO public.transactions (id, owner_user, name, created_at)
VALUES (
  '00000000-0000-0000-0000-000000000000'::uuid,
  '00000000-0000-0000-0000-000000000000'::uuid,
  'MVP Test Transaction',
  NOW()
) ON CONFLICT (id) DO NOTHING;

-- Verify it was created
SELECT * FROM public.transactions WHERE id = '00000000-0000-0000-0000-000000000000';
