<!-- a7f428f1-b923-45a3-9193-2287f3f46bb3 adbf5e89-dcef-4980-9df6-1ce07be66f31 -->
# Transaction & Negotiation Orchestrators - Production Implementation

## Critical Fixes & Architecture

This plan addresses all must-fix blockers identified in code review and implements a transparent, math-grounded consensus engine.

## Phase 1: Database Schema (Production-Ready)

### 1.1 Core Migration with Integrity Fixes

**File**: `supabase/migrations/008_negotiation_state.sql`

**Must-Fix Items Addressed:**

- UUID extension enabled
- Postgres enums for type safety
- Foreign key constraints with CASCADE/SET NULL
- UNIQUE constraints on critical tables
- Auto-updating timestamps via triggers
- Performance indexes
- RLS policies for privacy
- Clause dependency graph
- Policy constraints registry

**Key Tables:**

- `clause_instances` - Runtime clause values with schema versioning
- `conversation_state` - Shared turn-by-turn history
- `private_negotiation_state` - Per-party reservations (RLS protected)
- `leverage_snapshots` - Normalized leverage per round
- `concessions` - Directional deltas with utility impact
- `trade_proposals` - Cross-clause packages with evaluation
- `settlements` - Final packages with version for optimistic locking
- `clause_edges` - Dependency graph for validation
- `policy_constraints` - Hard legal and template constraints

### 1.2 Pydantic Request/Response Models

**File**: `backend/api/models/schemas.py`

**Must-Fix:** Add proper request validation models (not raw dicts)

**New Models:**

- `ProposeClauseRequest` - Validated proposal payload
- `TradeProposalRequest` - Validated trade payload with if/then
- `SettlementRequest` - With expected_version for optimistic locking
- `PrivateNegotiationState` - Reservation values model
- `ClauseEdge` - Dependency model
- `PolicyConstraint` - Constraint model

## Phase 2: Core Engines (Corrected Logic)

### 2.1 Fixed NegotiationOrchestrator

**File**: `backend/api/engine/negotiation_orchestrator.py`

**Must-Fix Items:**

1. Initialize `self.utility_engine = UtilityEngine()` in `__init__`
2. Initialize `self.policy_engine = PolicyEngine(supabase_client)` in `__init__`
3. Implement `_calculate_midpoint` with field-aware logic:

   - Exclusivity: weighted average of `period_days`
   - Vesting: weighted average of `cliff_months`, handle `vesting_months`
   - Preemption: boolean/enum logic (favor higher leverage)

4. Implement `_check_reservation_violation` using `private_negotiation_state`
5. Add `_weighted_midpoint` helper for clause-specific calculations

**New Methods:**

- `propose_turn()` - Record turn with state frame
- `counter_turn()` - Check convergence, detect trade opportunities
- `_build_explain_card()` - Transparent math card
- `_calculate_midpoint()` - Field-aware weighted averaging
- `_check_reservation_violation()` - Query private state
- `_get_last_offer()` - Fetch opposing party's last offer
- `_get_next_turn_no()` - Auto-increment turn counter

### 2.2 Fixed TradeEngine

**File**: `backend/api/engine/trade_engine.py`

**Must-Fix Items:**

1. Fix `_build_search_space` to guard against `step = 0`:
   ```python
   step = max(1, (max_val - min_val) // 4)
   ```

2. Fix fairness calculation in `settle_transaction` to use actual current utilities, not `50.0, 50.0`
3. Add `_validate_package()` to check clause dependencies via `clause_edges`
4. Add `_narrow_search_space()` for trade hints
5. Add `_generate_combinations()` with constraint pruning

**New Methods:**

- `explore_trades()` - Pareto frontier search
- `_build_search_space()` - Discrete grid with guards
- `_validate_package()` - Check clause_edges and policy_constraints
- `_calculate_fairness()` - Balanced gain ratio
- `_narrow_search_space()` - Focus around trade hint

### 2.3 TransactionOrchestrator

**File**: `backend/api/engine/transaction_orchestrator.py`

**Must-Fix:** Proper initialization and context building

**Key Methods:**

- `initialize_transaction()` - Create clause instances, compute leverage
- `negotiate_clause()` - Delegate to NegotiationOrchestrator, detect trades
- `propose_trade()` - Evaluate via TradeEngine
- `settle_transaction()` - With optimistic locking (version check)
- `_compute_leverage_snapshot()` - Normalize to sum=1.0, time-decay
- `_get_current_terms()` - Fetch from clause_instances
- `_build_context()` - Assemble NegotiationContext

### 2.4 Enhanced UtilityEngine

**File**: `backend/api/engine/utility.py` (enhance existing)

**Quality Improvements:**

- Normalize per-clause utilities to [0, 100]
- Weighted sum with explicit weights visible in ExplainCard
- Handle time-decay for leverage (cost of delay)
- Add `get_utilities()` method that returns both parties' scores

### 2.5 ConcessionLedger

**File**: `backend/api/engine/concession_ledger.py` (new)

Track directional deltas with utility-weighted magnitude:

- `record_concession()` - Store delta with utility impact
- `get_concession_balance()` - Per-party running total
- `_calculate_utility_impact()` - Normalize by party's sensitivity

## Phase 3: API Routes (Validated Payloads)

### 3.1 Transaction Routes

**File**: `backend/api/routes/transactions.py`

**Must-Fix:** Use Pydantic request models, add idempotency

**Endpoints:**

- `POST /{transaction_id}/initialize` - With `InitializeRequest`
- `POST /{transaction_id}/clauses/{clause_key}/propose` - With `ProposeClauseRequest`
- `POST /{transaction_id}/trade` - With `TradeProposalRequest`
- `POST /{transaction_id}/settle` - With `SettlementRequest` (includes `expected_version`)
- `GET /{transaction_id}/conversation/{clause_key}` - History
- `GET /{transaction_id}/leverage` - Latest snapshot
- `GET /{transaction_id}/concessions` - Ledger

**Idempotency:** Settle endpoint checks version, returns 409 Conflict if mismatch

## Phase 4: Frontend Components

### 4.1 NegotiationRoom

**File**: `frontend/src/components/NegotiationRoom.tsx`

3-column layout: ClauseRail | ConversationHistory + OfferPanel | ExplainCard + TradeBuilder + ConcessionLedger

### 4.2 ExplainCard

**File**: `frontend/src/components/ExplainCard.tsx`

Shows: inputs, leverage (normalized), utilities (0-100), midpoint calculation, constraints hit, rationale

### 4.3 TradeBuilder

**File**: `frontend/src/components/TradeBuilder.tsx`

IF/THEN clause selector with value editors

### 4.4 ConcessionLedger

**File**: `frontend/src/components/ConcessionLedger.tsx`

Running tally of concessions per party with utility impact

## Phase 5: Example Flow

### 5.1 Exclusivity Negotiation

**File**: `backend/api/examples/exclusivity_flow.py`

Demonstrates:

1. Transaction initialization
2. Leverage computation (Company 0.42, Investor 0.58)
3. Opening positions (90 days vs 30 days)
4. Midpoint calculation (63 days)
5. Reservation violation detected (Company max 45)
6. Trade exploration (60 days exclusivity for 6-month cliff)
7. ExplainCard review
8. Settlement with scorecard

## Phase 6: Testing

### 6.1 Unit Tests

**Files:**

- `backend/tests/test_trade_engine.py` - Pareto search, fairness, step guards
- `backend/tests/test_negotiation_orchestrator.py` - Midpoint logic, reservation checks
- `backend/tests/test_utility_engine.py` - Normalization, weighted sums
- `backend/tests/test_concession_ledger.py` - Delta tracking, balance

### 6.2 Integration Tests

**File**: `backend/tests/test_negotiation_flow.py`

End-to-end: initialize → propose → counter → trade → settle

### 6.3 Property-Based Tests

**File**: `backend/tests/test_properties.py`

Invariants:

- Trades never violate reservations
- Utilities are monotonic
- Fairness bounded [0, 1]
- Leverage sums to 1.0
- Step size always >= 1

## Implementation Order

1. **Phase 1.1** - Database migration with all fixes
2. **Phase 1.2** - Pydantic models with request validation
3. **Phase 2.1** - Fixed NegotiationOrchestrator
4. **Phase 2.2** - Fixed TradeEngine
5. **Phase 2.3** - TransactionOrchestrator
6. **Phase 2.4** - Enhanced UtilityEngine
7. **Phase 2.5** - ConcessionLedger
8. **Phase 3.1** - API routes with validation
9. **Phase 4** - Frontend components
10. **Phase 5** - Example flow
11. **Phase 6** - Tests

## Key Files

**New:**

- `supabase/migrations/008_negotiation_state.sql`
- `backend/api/engine/transaction_orchestrator.py`
- `backend/api/engine/trade_engine.py`
- `backend/api/engine/concession_ledger.py`
- `backend/api/examples/exclusivity_flow.py`
- `frontend/src/components/NegotiationRoom.tsx`
- `frontend/src/components/ExplainCard.tsx`
- `frontend/src/components/TradeBuilder.tsx`
- `frontend/src/components/ConcessionLedger.tsx`

**Modified:**

- `backend/api/models/schemas.py` - Add request models, private state, edges, constraints
- `backend/api/engine/negotiation_orchestrator.py` - Fix initialization, add multi-turn
- `backend/api/engine/utility.py` - Normalize utilities, time-decay
- `backend/api/routes/transactions.py` - Add validated endpoints

## Must-Fix Checklist

**SQL:**

- [x] UUID extension enabled
- [x] Enums for party_role, clause_status, trade_status
- [x] Foreign keys with CASCADE/SET NULL
- [x] UNIQUE constraints (transaction_id, clause_key), (transaction_id, round_no)
- [x] Auto-update triggers for updated_at
- [x] Performance indexes on all query paths
- [x] RLS policies for privacy
- [x] clause_edges table for dependencies
- [x] policy_constraints table

**Orchestrator:**

- [x] Initialize utility_engine in **init**
- [x] Initialize policy_engine in **init**
- [x] Implement _calculate_midpoint with field-awareness
- [x] Implement _check_reservation_violation
- [x] Guard step size in search space (step >= 1)
- [x] Fix fairness to use actual current utilities

**API:**

- [x] Pydantic request models (not raw dicts)
- [x] Optimistic locking on settle (expected_version)
- [x] Idempotency on critical endpoints

**Quality:**

- [x] Normalize utilities to [0, 100]
- [x] Normalize leverage to sum=1.0
- [x] Concession tracking with utility impact
- [x] Constraint validation via clause_edges
- [x] Versioning on clause schemas
- [x] Observability (audit_log with ExplainCards)

This plan creates a production-ready, transparent, math-grounded consensus engine.

### To-dos

- [ ] Create 008_negotiation_state.sql with UUID extension, enums, FK constraints, UNIQUE constraints, triggers, indexes, RLS, clause_edges, policy_constraints
- [ ] Add Pydantic request models (ProposeClauseRequest, TradeProposalRequest, SettlementRequest), PrivateNegotiationState, ClauseEdge, PolicyConstraint to schemas.py
- [ ] Fix NegotiationOrchestrator: initialize utility_engine and policy_engine, implement _calculate_midpoint with field-awareness, _check_reservation_violation, add multi-turn methods
- [ ] Fix TradeEngine: guard step size (step >= 1), fix fairness calculation to use actual utilities, implement _validate_package with clause_edges, add _narrow_search_space
- [ ] Implement TransactionOrchestrator with proper initialization, context building, leverage normalization (sum=1.0), optimistic locking on settle
- [ ] Enhance UtilityEngine: normalize per-clause to [0,100], weighted sum with explicit weights, time-decay for leverage, add get_utilities() method
- [ ] Create ConcessionLedger: record_concession(), get_concession_balance(), _calculate_utility_impact() with normalization
- [ ] Add transaction API routes with Pydantic validation, idempotency on settle (version check), all endpoints from plan
- [ ] Build NegotiationRoom component with 3-column layout: ClauseRail, ConversationHistory+OfferPanel, ExplainCard+TradeBuilder+ConcessionLedger
- [ ] Build ExplainCard showing inputs, normalized leverage, utilities [0-100], midpoint calculation, constraints, rationale
- [ ] Build TradeBuilder with IF/THEN clause selector and value editors
- [ ] Build ConcessionLedger component showing running tally per party with utility impact
- [ ] Implement exclusivity_flow.py demonstrating full flow: init, leverage, propose, counter, midpoint, reservation violation, trade, settle
- [ ] Write unit tests: trade_engine (pareto, fairness, step guards), negotiation_orchestrator (midpoint, reservations), utility_engine (normalization), concession_ledger
- [ ] Write integration tests for full negotiation flow: initialize → propose → counter → trade → settle
- [ ] Write property-based tests verifying invariants: no reservation violations, utilities monotonic, fairness [0,1], leverage sums to 1.0, step >= 1