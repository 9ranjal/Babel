-- ============================================================================
-- Create Test User for Development
-- Migration: 004_test_user.sql
-- Description: Insert placeholder user for testing without authentication
-- ============================================================================

-- Insert test user (if not exists)
INSERT INTO public.users (user_id, email, created_at)
VALUES (
  '00000000-0000-0000-0000-000000000000'::uuid,
  'test@termcraft.dev',
  NOW()
)
ON CONFLICT (user_id) DO NOTHING;

-- Verify test user exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.users WHERE user_id = '00000000-0000-0000-0000-000000000000'::uuid) THEN
    RAISE NOTICE '✅ Test user created successfully';
  ELSE
    RAISE EXCEPTION '❌ Failed to create test user';
  END IF;
END $$;

