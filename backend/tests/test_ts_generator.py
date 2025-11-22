"""Tests for term sheet generator."""
from __future__ import annotations

import pytest

from api.models.deal_schemas import DealConfig, DealOverrides, get_base_deal_config
from api.services.ts_generator.clause_selector import select_clause_templates
from api.services.ts_generator.renderer import render_term_sheet


def test_deal_overrides_parsing():
    """Test that DealOverrides can be created with partial data."""
    overrides = DealOverrides(
        investment_amount=5000000,
        pre_money_valuation=25000000,
        investor_board_seats=1,
    )
    assert overrides.investment_amount == 5000000
    assert overrides.pre_money_valuation == 25000000
    assert overrides.investor_board_seats == 1
    assert overrides.currency is None  # Not specified


def test_deal_config_merges_defaults():
    """Test that DealConfig merges overrides with defaults."""
    base = get_base_deal_config()
    assert base.currency == "USD"
    assert base.liquidation_preference_multiple == 1.0
    assert base.liquidation_preference_participation == "non_participating"
    assert base.anti_dilution_type == "broad_wa"


def test_deal_config_post_money_calculation():
    """Test that post_money_valuation is calculated if not provided."""
    deal = DealConfig(
        investment_amount=5000000,
        pre_money_valuation=25000000,
        investor_board_seats=1,
    )
    assert deal.post_money_valuation == 30000000  # 25M + 5M


def test_clause_selection_basic():
    """Test clause selection for a basic deal."""
    deal = DealConfig(
        investment_amount=5000000,
        pre_money_valuation=25000000,
        currency="USD",
        investor_board_seats=1,
        liquidation_preference_multiple=1.0,
        liquidation_preference_participation="non_participating",
        anti_dilution_type="broad_wa",
    )
    clause_ids = select_clause_templates(deal)
    
    # Should include investment amount
    assert "ts_investment_amount_v1" in clause_ids
    # Should include valuation
    assert "ts_valuation_v1" in clause_ids
    # Should include liquidation preference
    assert "ts_liqpref_1x_np_v1" in clause_ids
    # Should include anti-dilution
    assert "ts_anti_dilution_broad_wa_v1" in clause_ids


def test_clause_selection_safe():
    """Test clause selection for SAFE instrument."""
    deal = DealConfig(
        investment_amount=2000000,
        instrument_type="SAFE",
        currency="USD",
        observer_seats=1,
    )
    clause_ids = select_clause_templates(deal)
    
    # Should NOT include liquidation preference for SAFE
    assert not any("liqpref" in tid for tid in clause_ids)
    # Should NOT include anti-dilution for SAFE
    assert not any("anti_dilution" in tid for tid in clause_ids)
    # Should include investment amount
    assert "ts_investment_amount_v1" in clause_ids


def test_render_term_sheet_safe_excludes_clauses():
    """Test that rendered SAFE term sheet does not contain liquidation preference or anti-dilution."""
    deal = DealConfig(
        investment_amount=2000000,
        instrument_type="SAFE",
        currency="USD",
        observer_seats=1,
        # Explicitly set these to ensure they would be included if not for SAFE filtering
        liquidation_preference_multiple=1.0,
        liquidation_preference_participation="non_participating",
        anti_dilution_type="broad_wa",
    )
    clause_ids = select_clause_templates(deal)
    rendered = render_term_sheet(deal, clause_ids)
    
    # Should NOT contain liquidation preference wording
    assert "Liquidation Preference" not in rendered
    assert "liquidation" not in rendered.lower()
    # Should NOT contain anti-dilution wording
    assert "Anti-Dilution" not in rendered
    assert "anti-dilution" not in rendered.lower()
    # Should contain investment amount
    assert "Investment Amount" in rendered or "$2,000,000" in rendered


def test_clause_selection_no_board_seats():
    """Test clause selection when investor has no board seats."""
    deal = DealConfig(
        investment_amount=5000000,
        pre_money_valuation=25000000,
        currency="USD",
        investor_board_seats=0,
    )
    clause_ids = select_clause_templates(deal)
    
    # Should use "no seats" template
    assert "ts_board_no_seats_v1" in clause_ids
    # Should NOT include regular board composition
    assert not any(tid.startswith("ts_board_composition") for tid in clause_ids)


def test_render_term_sheet():
    """Test term sheet rendering."""
    deal = DealConfig(
        investment_amount=5000000,
        pre_money_valuation=25000000,
        currency="USD",
        round_type="Seed",
        instrument_type="CCPS",
        investor_board_seats=1,
        liquidation_preference_multiple=1.0,
        liquidation_preference_participation="non_participating",
        anti_dilution_type="broad_wa",
    )
    clause_ids = select_clause_templates(deal)
    rendered = render_term_sheet(deal, clause_ids)
    
    # Should contain term sheet header
    assert "# Term Sheet" in rendered
    # Should contain investment amount
    assert "Investment Amount" in rendered or "$5,000,000" in rendered
    # Should contain valuation
    assert "Pre-Money Valuation" in rendered or "Valuation" in rendered
    # Should contain sections
    assert "## Economics" in rendered
    assert "## Control & Governance" in rendered


@pytest.mark.asyncio
async def test_generate_term_sheet_integration(monkeypatch):
    """Integration test for full term sheet generation with mocked LLM."""
    from api.services.ts_generator.graph import parse_nl_node
    from api.services.ts_generator import generate_term_sheet
    from api.models.deal_schemas import DealOverrides
    
    # Mock the LLM parsing to return deterministic overrides
    async def mock_parse_nl_node(state):
        # Simulate parsing "5M at 25 premoney, 1 board seat"
        overrides = DealOverrides(
            investment_amount=5000000,
            pre_money_valuation=25000000,
            investor_board_seats=1,
        )
        return {**state, "overrides": overrides}
    
    # Monkeypatch parse_nl_node
    monkeypatch.setattr("api.services.ts_generator.graph.parse_nl_node", mock_parse_nl_node)
    
    # Test with simple input
    result = await generate_term_sheet("5M at 25 premoney, 1 board seat")
    
    assert "term_sheet" in result
    assert "deal_config" in result
    assert "validation_errors" in result
    
    # Check that deal config was parsed
    deal_config = result["deal_config"]
    assert deal_config.get("investment_amount") == 5000000
    assert deal_config.get("pre_money_valuation") == 25000000
    assert deal_config.get("investor_board_seats") == 1
    
    # Check that term sheet was generated
    assert len(result["term_sheet"]) > 0
    assert "Term Sheet" in result["term_sheet"]


@pytest.mark.asyncio
async def test_generate_term_sheet_safe(monkeypatch):
    """Test term sheet generation for SAFE with mocked LLM."""
    from api.services.ts_generator.graph import parse_nl_node
    from api.services.ts_generator import generate_term_sheet
    from api.models.deal_schemas import DealOverrides
    
    # Mock the LLM parsing to return deterministic overrides for SAFE
    async def mock_parse_nl_node(state):
        # Simulate parsing "2M SAFE at 8 cap, no discount, 1 board observer"
        overrides = DealOverrides(
            investment_amount=2000000,
            instrument_type="SAFE",
            observer_seats=1,
        )
        return {**state, "overrides": overrides}
    
    # Monkeypatch parse_nl_node
    monkeypatch.setattr("api.services.ts_generator.graph.parse_nl_node", mock_parse_nl_node)
    
    result = await generate_term_sheet("2M SAFE at 8 cap, no discount, 1 board observer")
    
    assert "term_sheet" in result
    deal_config = result["deal_config"]
    assert deal_config.get("instrument_type") == "SAFE"
    assert deal_config.get("investment_amount") == 2000000
    
    # Verify SAFE-specific exclusions
    assert "Liquidation Preference" not in result["term_sheet"]
    assert "Anti-Dilution" not in result["term_sheet"]

