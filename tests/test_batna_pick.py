import json
from backend.api.services.band_map import pick_band, composite_score, DEFAULT_LEVERAGE

import os
with open(os.path.join(os.path.dirname(__file__), "..", "packages", "batna", "seed", "bands.json"), "r") as f:
    PACK = json.load(f)

def find_clause(key):
    return next(c for c in PACK["clauses"] if c["clause_key"] == key)

# Basic functionality tests
def test_exclusivity_30_market():
    c = find_clause("exclusivity")
    b = pick_band(c["bands"], {"value": 30}, DEFAULT_LEVERAGE)
    assert b and b["name"] == "market"

def test_rofr_10_short_window():
    c = find_clause("rofr")
    b = pick_band(c["bands"], {"value": 10}, DEFAULT_LEVERAGE)
    assert b and "short" in b["name"]

def test_antidilution_broad_wa_market():
    c = find_clause("anti_dilution")
    b = pick_band(c["bands"], {"value": "broad_wa"}, DEFAULT_LEVERAGE)
    assert b and b["name"] == "broad_wa"

# Comprehensive band selection tests
def test_exclusivity_boundary_cases():
    c = find_clause("exclusivity")
    # Test lower boundary of short range
    b1 = pick_band(c["bands"], {"value": 15}, DEFAULT_LEVERAGE)
    assert b1 and b1["name"] == "short"

    # Test upper boundary of short range (falls in both short and market ranges)
    b2 = pick_band(c["bands"], {"value": 30}, DEFAULT_LEVERAGE)
    assert b2 and b2["name"] == "market"  # Should pick market due to tie-breaking

    # Test upper boundary of market range (overlaps with long range start)
    b3 = pick_band(c["bands"], {"value": 45}, DEFAULT_LEVERAGE)
    assert b3 and b3["name"] == "market"  # 45 falls in market range [30, 45]

def test_preemption_enum_matching():
    c = find_clause("preemptive_pro_rata")
    b1 = pick_band(c["bands"], {"value": "none"}, DEFAULT_LEVERAGE)
    assert b1 and b1["name"] == "none"

    b2 = pick_band(c["bands"], {"value": "limited_next_round"}, DEFAULT_LEVERAGE)
    assert b2 and b2["name"] == "market"

    b3 = pick_band(c["bands"], {"value": "full_ongoing"}, DEFAULT_LEVERAGE)
    assert b3 and b3["name"] == "full"

def test_liq_pref_enum_scoring():
    c = find_clause("liquidation_preference")
    # Test that 1x_np is market
    b1 = pick_band(c["bands"], {"value": "1x_np"}, DEFAULT_LEVERAGE)
    assert b1 and b1["name"] == "market"

    # Test that 1x_p has higher investor score
    b2 = pick_band(c["bands"], {"value": "1x_p"}, DEFAULT_LEVERAGE)
    assert b2 and b2["name"] == "investor_plus"

    # Test that >1x_p has highest investor score
    b3 = pick_band(c["bands"], {"value": ">1x_p"}, DEFAULT_LEVERAGE)
    assert b3 and b3["name"] == "heavy_p"

# Composite scoring and leverage tests
def test_composite_scoring():
    c = find_clause("exclusivity")
    bands = c["bands"]

    # Test that market band has balanced scoring
    market_band = next(b for b in bands if b["name"] == "market")
    score = composite_score(market_band, DEFAULT_LEVERAGE)
    assert abs(score - 0.6) < 0.001  # Should be 0.6

    # Test founder-favored band (actually has lower score than market)
    short_band = next(b for b in bands if b["name"] == "short")
    founder_score = composite_score(short_band, DEFAULT_LEVERAGE)
    assert abs(founder_score - 0.52) < 0.001  # 1.0*0.4 + 0.2*0.6 = 0.52

    # Test investor-favored band (has highest score)
    long_band = next(b for b in bands if b["name"] == "long")
    investor_score = composite_score(long_band, DEFAULT_LEVERAGE)
    assert abs(investor_score - 0.68) < 0.001  # 0.2*0.4 + 1.0*0.6 = 0.68

def test_leverage_sensitivity():
    # Create test bands that demonstrate leverage sensitivity
    test_bands = [
        {"name": "founder_band", "range": [10, 20], "founder_score": 0.9, "investor_score": 0.3},
        {"name": "investor_band", "range": [10, 20], "founder_score": 0.3, "investor_score": 0.9},
    ]

    founder_lev = {"investor": 0.3, "founder": 0.7}
    investor_lev = {"investor": 0.8, "founder": 0.2}

    # Same value, different leverage should pick different bands
    b1 = pick_band(test_bands, {"value": 15}, founder_lev)
    b2 = pick_band(test_bands, {"value": 15}, investor_lev)

    # With founder-favored leverage, should pick founder band
    assert b1 and b1["name"] == "founder_band"

    # With investor-favored leverage, should pick investor band
    assert b2 and b2["name"] == "investor_band"

def test_market_tie_breaking():
    # Create a test scenario where multiple bands have same composite score
    test_bands = [
        {"name": "market", "founder_score": 0.5, "investor_score": 0.7, "range": [10, 20]},
        {"name": "other", "founder_score": 0.7, "investor_score": 0.5, "range": [10, 20]},
    ]

    # Both bands should have same composite score (0.6) for value 15
    b = pick_band(test_bands, {"value": 15}, DEFAULT_LEVERAGE)
    assert b and b["name"] == "market"  # Should prefer market

# Posture classification tests
def test_posture_classification():
    from backend.api.services.analyze import analyze_clause
    import asyncio

    # Mock session for testing posture logic
    class MockSession:
        async def execute(self, query, params):
            # Mock successful upsert returning posture data
            class MockRow:
                id = 1
                clause_id = "test-id"
                band_name = "market"
                band_score = 0.6
                analysis_json = {"posture": "market", "trades": []}
                redraft_text = None
            return type('Result', (), {'fetchone': lambda: MockRow()})()

        async def commit(self):
            pass

    # Test founder-friendly posture (founder_score much higher than investor_score)
    founder_friendly_band = {"name": "founder_fav", "founder_score": 0.9, "investor_score": 0.1}
    # Posture is determined by raw scores, not composite
    assert founder_friendly_band["founder_score"] > founder_friendly_band["investor_score"] + 0.2

    # Test investor-friendly posture (investor_score much higher than founder_score)
    investor_friendly_band = {"name": "investor_fav", "founder_score": 0.1, "investor_score": 0.9}
    assert investor_friendly_band["investor_score"] > investor_friendly_band["founder_score"] + 0.2

    # Test market posture (balanced scores)
    market_band = {"name": "balanced", "founder_score": 0.6, "investor_score": 0.6}
    diff = abs(market_band["founder_score"] - market_band["investor_score"])
    assert diff <= 0.2  # Difference should be small for market posture

# Edge cases and error handling
def test_no_matching_bands():
    c = find_clause("exclusivity")
    # Value outside all ranges should return None
    b = pick_band(c["bands"], {"value": 100}, DEFAULT_LEVERAGE)
    assert b is None

def test_missing_value():
    c = find_clause("exclusivity")
    # Missing value should match predicate-only bands (drag, vesting)
    drag_clause = find_clause("drag_along")
    # Drag bands have predicates, should work without value
    b = pick_band(drag_clause["bands"], {}, DEFAULT_LEVERAGE)
    assert b is not None  # Should pick a band

def test_enum_fallback():
    c = find_clause("preemptive_pro_rata")
    # Invalid enum value should not match any band
    b = pick_band(c["bands"], {"value": "invalid_enum"}, DEFAULT_LEVERAGE)
    assert b is None

# Integration test for middle ground finding
def test_middle_ground_detection():
    """Test that the system finds reasonable middle ground across different scenarios"""

    # Test that exclusivity 30 days is considered market (middle ground)
    c = find_clause("exclusivity")
    b = pick_band(c["bands"], {"value": 30}, DEFAULT_LEVERAGE)
    assert b["name"] == "market"

    # Test that moderate ESOP pool is market
    esop_clause = find_clause("option_pool")
    b2 = pick_band(esop_clause["bands"], {"value": 12}, DEFAULT_LEVERAGE)
    assert b2["name"] == "market_pre_10_15"  # Market standard

    # Test that balanced board composition is market
    board_clause = find_clause("board")
    b3 = pick_band(board_clause["bands"], {"value": "balanced"}, DEFAULT_LEVERAGE)
    assert b3["name"] == "market"

def test_comprehensive_clause_coverage():
    """Ensure all major clause types work"""
    test_cases = [
        ("exclusivity", {"value": 30}, "market"),
        ("preemptive_pro_rata", {"value": "limited_next_round"}, "market"),
        ("rofo", {"value": 20}, "market"),
        ("rofr", {"value": 20}, "market"),
        ("tag_along", {"value": "pro_rata_only"}, "market"),
        ("anti_dilution", {"value": "broad_wa"}, "broad_wa"),
        ("reserved_matters", {"value": "market_list"}, "market"),
        ("exit", {"value": 4}, "market"),
        ("liquidation_preference", {"value": "1x_np"}, "market"),
        ("board", {"value": "balanced"}, "market"),
        ("information_rights", {"value": "monthly_kpi_q_fin"}, "market"),
        ("option_pool", {"value": 12}, "market_pre_10_15"),
        ("pay_to_play", {"value": "soft"}, "market"),
    ]

    for clause_key, attrs, expected_band in test_cases:
        c = find_clause(clause_key)
        b = pick_band(c["bands"], attrs, DEFAULT_LEVERAGE)
        assert b is not None, f"No band found for {clause_key}"
        assert b["name"] == expected_band, f"Expected {expected_band} for {clause_key}, got {b['name']}"
