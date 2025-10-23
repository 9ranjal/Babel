-- ============================================================================
-- Termcraft AI - Seed Data
-- Migration: 002_seed_data.sql
-- Description: Inserts initial clause library and market benchmarks
-- ============================================================================

-- ============================================================================
-- 1. CLAUSE LIBRARY - Core Term Sheet Clauses
-- ============================================================================

INSERT INTO public.clause_library (clause_key, param_schema, constraints, templates, description)
VALUES
  (
    'vesting',
    '{
      "vesting_months": "integer",
      "cliff_months": "integer"
    }'::jsonb,
    '{
      "min": {"vesting_months": 0, "cliff_months": 0},
      "max": {"vesting_months": 48, "cliff_months": 12},
      "non_negotiable_for_investor": false,
      "typical_range": {"vesting_months": [36, 48], "cliff_months": [0, 12]}
    }'::jsonb,
    '{
      "md": "**Vesting:** {{vesting_months}} months with {{cliff_months}}-month cliff",
      "docx": "The shares shall vest over {{vesting_months}} months, with a {{cliff_months}}-month cliff period."
    }'::jsonb,
    'Founder equity vesting schedule to ensure long-term commitment'
  ),
  
  (
    'valuation_cap',
    '{
      "cap_amount_usd": "number"
    }'::jsonb,
    '{
      "min": {"cap_amount_usd": 100000},
      "max": {"cap_amount_usd": 50000000},
      "non_negotiable_for_investor": false,
      "typical_range": {"cap_amount_usd": [3000000, 15000000]}
    }'::jsonb,
    '{
      "md": "**Valuation Cap:** ${{cap_amount_usd | number_format}}",
      "docx": "The valuation cap for this convertible note shall be USD {{cap_amount_usd | number_format}}."
    }'::jsonb,
    'Maximum company valuation for note conversion (for SAFE/convertible notes)'
  ),
  
  (
    'discount_rate',
    '{
      "discount_percentage": "number"
    }'::jsonb,
    '{
      "min": {"discount_percentage": 0},
      "max": {"discount_percentage": 30},
      "non_negotiable_for_investor": false,
      "typical_range": {"discount_percentage": [15, 25]}
    }'::jsonb,
    '{
      "md": "**Discount Rate:** {{discount_percentage}}%",
      "docx": "Investors shall receive a {{discount_percentage}}% discount on the next equity round price."
    }'::jsonb,
    'Discount on next round price for early investors'
  ),
  
  (
    'pro_rata_rights',
    '{
      "enabled": "boolean",
      "threshold_ownership_pct": "number"
    }'::jsonb,
    '{
      "min": {"threshold_ownership_pct": 0},
      "max": {"threshold_ownership_pct": 100},
      "non_negotiable_for_investor": true,
      "typical_range": {"threshold_ownership_pct": [1, 5]}
    }'::jsonb,
    '{
      "md": "**Pro Rata Rights:** {{#if enabled}}Enabled for investors holding ≥{{threshold_ownership_pct}}%{{else}}Not granted{{/if}}",
      "docx": "{{#if enabled}}Investors holding at least {{threshold_ownership_pct}}% shall have pro rata participation rights in future rounds.{{else}}Pro rata rights are not granted.{{/if}}"
    }'::jsonb,
    'Right for investors to maintain ownership percentage in future rounds'
  ),
  
  (
    'liquidation_preference',
    '{
      "multiple": "number",
      "participating": "boolean"
    }'::jsonb,
    '{
      "min": {"multiple": 1},
      "max": {"multiple": 3},
      "non_negotiable_for_investor": true,
      "typical_range": {"multiple": [1, 1.5]}
    }'::jsonb,
    '{
      "md": "**Liquidation Preference:** {{multiple}}x {{#if participating}}participating{{else}}non-participating{{/if}}",
      "docx": "Investors shall have a {{multiple}}x liquidation preference, {{#if participating}}with{{else}}without{{/if}} participation rights."
    }'::jsonb,
    'Priority and multiple for investor payouts in exit scenarios'
  ),
  
  (
    'board_seats',
    '{
      "investor_seats": "integer",
      "founder_seats": "integer",
      "independent_seats": "integer"
    }'::jsonb,
    '{
      "min": {"investor_seats": 0, "founder_seats": 1, "independent_seats": 0},
      "max": {"investor_seats": 5, "founder_seats": 5, "independent_seats": 3},
      "non_negotiable_for_investor": false,
      "typical_range": {
        "investor_seats": [1, 2],
        "founder_seats": [2, 3],
        "independent_seats": [0, 1]
      }
    }'::jsonb,
    '{
      "md": "**Board Composition:** {{founder_seats}} founder, {{investor_seats}} investor, {{independent_seats}} independent",
      "docx": "The Board of Directors shall consist of {{founder_seats}} founder-appointed, {{investor_seats}} investor-appointed, and {{independent_seats}} independent directors."
    }'::jsonb,
    'Board of directors composition and control'
  ),
  
  (
    'information_rights',
    '{
      "monthly_financials": "boolean",
      "quarterly_board_meetings": "boolean",
      "annual_budget_approval": "boolean"
    }'::jsonb,
    '{
      "non_negotiable_for_investor": true
    }'::jsonb,
    '{
      "md": "**Information Rights:** {{#if monthly_financials}}Monthly financials{{/if}}{{#if quarterly_board_meetings}}, Quarterly board meetings{{/if}}{{#if annual_budget_approval}}, Annual budget approval{{/if}}",
      "docx": "Investors shall receive: {{#if monthly_financials}}monthly financial statements{{/if}}{{#if quarterly_board_meetings}}, attend quarterly board meetings{{/if}}{{#if annual_budget_approval}}, and approve annual budgets{{/if}}."
    }'::jsonb,
    'Information and oversight rights for investors'
  ),
  
  (
    'anti_dilution',
    '{
      "protection_type": "enum",
      "carveout_option_pool_pct": "number"
    }'::jsonb,
    '{
      "allowed_values": {
        "protection_type": ["none", "full-ratchet", "weighted-average-broad", "weighted-average-narrow"]
      },
      "min": {"carveout_option_pool_pct": 0},
      "max": {"carveout_option_pool_pct": 20},
      "non_negotiable_for_investor": true,
      "typical_range": {"carveout_option_pool_pct": [10, 15]}
    }'::jsonb,
    '{
      "md": "**Anti-Dilution:** {{protection_type}} with {{carveout_option_pool_pct}}% option pool carveout",
      "docx": "Anti-dilution protection shall be {{protection_type}} with a {{carveout_option_pool_pct}}% carveout for the employee option pool."
    }'::jsonb,
    'Protection against dilution in down rounds'
  );

-- ============================================================================
-- 2. MARKET BENCHMARKS - Industry Standard Data
-- ============================================================================

-- Vesting benchmarks
INSERT INTO public.market_benchmarks (clause_key, stage, region, p25, p50, p75, asof_date, source)
VALUES
  ('vesting', 'seed', 'US', 36, 48, 48, '2024-01-01', 'Y Combinator Standard'),
  ('vesting', 'seed', 'IN', 36, 36, 48, '2024-01-01', 'India Startup Survey 2024'),
  ('vesting', 'series-a', 'US', 36, 48, 48, '2024-01-01', 'NVCA Model Docs'),
  ('vesting', 'series-a', 'IN', 36, 48, 48, '2024-01-01', 'India VC Association');

-- Valuation cap benchmarks (in millions USD)
INSERT INTO public.market_benchmarks (clause_key, stage, region, p25, p50, p75, asof_date, source)
VALUES
  ('valuation_cap', 'seed', 'US', 5000000, 8000000, 12000000, '2024-01-01', 'Carta Market Data 2024'),
  ('valuation_cap', 'seed', 'IN', 2000000, 4000000, 6000000, '2024-01-01', 'Inc42 India Funding Report'),
  ('valuation_cap', 'pre-seed', 'US', 3000000, 5000000, 8000000, '2024-01-01', 'AngelList Data'),
  ('valuation_cap', 'pre-seed', 'IN', 1000000, 2000000, 3500000, '2024-01-01', 'Tracxn India Report');

-- Discount rate benchmarks
INSERT INTO public.market_benchmarks (clause_key, stage, region, p25, p50, p75, asof_date, source)
VALUES
  ('discount_rate', 'seed', 'US', 15, 20, 25, '2024-01-01', 'Y Combinator SAFE'),
  ('discount_rate', 'seed', 'IN', 15, 20, 25, '2024-01-01', 'India Angels Network'),
  ('discount_rate', 'pre-seed', 'US', 20, 25, 30, '2024-01-01', 'AngelList Standard'),
  ('discount_rate', 'pre-seed', 'IN', 20, 25, 30, '2024-01-01', 'LetsVenture Data');

-- Pro rata threshold benchmarks
INSERT INTO public.market_benchmarks (clause_key, stage, region, p25, p50, p75, asof_date, source)
VALUES
  ('pro_rata_rights', 'seed', 'US', 1, 2, 5, '2024-01-01', 'NVCA Standard'),
  ('pro_rata_rights', 'seed', 'IN', 1, 3, 5, '2024-01-01', 'IVCA Guidelines'),
  ('pro_rata_rights', 'series-a', 'US', 1, 1, 3, '2024-01-01', 'Carta Data'),
  ('pro_rata_rights', 'series-a', 'IN', 1, 2, 3, '2024-01-01', 'India VC Trends');

-- Liquidation preference multiples
INSERT INTO public.market_benchmarks (clause_key, stage, region, p25, p50, p75, asof_date, source)
VALUES
  ('liquidation_preference', 'seed', 'US', 1.0, 1.0, 1.0, '2024-01-01', 'Industry Standard'),
  ('liquidation_preference', 'seed', 'IN', 1.0, 1.0, 1.0, '2024-01-01', 'India Standard'),
  ('liquidation_preference', 'series-a', 'US', 1.0, 1.0, 1.5, '2024-01-01', 'NVCA Model'),
  ('liquidation_preference', 'series-a', 'IN', 1.0, 1.0, 1.0, '2024-01-01', 'IVCA Model');

-- Board seats benchmarks (investor seats)
INSERT INTO public.market_benchmarks (clause_key, stage, region, p25, p50, p75, asof_date, source)
VALUES
  ('board_seats', 'seed', 'US', 1, 1, 2, '2024-01-01', 'Seed Stage Governance'),
  ('board_seats', 'seed', 'IN', 0, 1, 1, '2024-01-01', 'India Seed Standard'),
  ('board_seats', 'series-a', 'US', 1, 2, 2, '2024-01-01', 'Series A Standard'),
  ('board_seats', 'series-a', 'IN', 1, 2, 2, '2024-01-01', 'India Series A Norm');

-- ============================================================================
-- 3. VERIFICATION QUERIES
-- ============================================================================

-- Verify clause library count
DO $$
DECLARE
  clause_count INT;
BEGIN
  SELECT COUNT(*) INTO clause_count FROM public.clause_library;
  RAISE NOTICE 'Clause library entries: %', clause_count;
END $$;

-- Verify market benchmarks count
DO $$
DECLARE
  benchmark_count INT;
BEGIN
  SELECT COUNT(*) INTO benchmark_count FROM public.market_benchmarks;
  RAISE NOTICE 'Market benchmark entries: %', benchmark_count;
END $$;

-- ============================================================================
-- SEED DATA COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Test queries against clause_library and market_benchmarks
-- 2. Create sample personas
-- 3. Test negotiation flow
-- ============================================================================

