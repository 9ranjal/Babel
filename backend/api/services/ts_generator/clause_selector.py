"""Clause selection logic for term sheet generation."""
from __future__ import annotations

from typing import List

from .templates import get_clause_templates

from api.models.deal_schemas import DealConfig


def select_clause_templates(deal: DealConfig) -> List[str]:
    """
    Select clause templates based on deal configuration.
    
    Returns a list of template IDs that should be included in the term sheet.
    """
    all_templates = get_clause_templates()
    selected_ids: List[str] = []
    seen_clause_keys: set[str] = set()

    # For SAFE instruments, exclude clauses that don't apply
    safe_excluded_clause_keys = set()
    if deal.instrument_type == "SAFE":
        safe_excluded_clause_keys = {"liquidation_preference", "anti_dilution"}

    # Special handling: if investor_board_seats is 0, prefer "no seats" template
    board_template_priority = None
    if deal.investor_board_seats == 0:
        board_template_priority = "ts_board_no_seats_v1"

    # Iterate through templates and select matching ones
    for template in all_templates:
        # Skip if we've already selected a template for this clause_key
        if template.clause_key in seen_clause_keys:
            continue

        # Skip SAFE-excluded clauses
        if template.clause_key in safe_excluded_clause_keys:
            continue

        # For board clause, if we have a priority template, only select that one
        if template.clause_key == "board" and board_template_priority:
            if template.template_id == board_template_priority and template.matches(deal):
                selected_ids.append(template.template_id)
                seen_clause_keys.add(template.clause_key)
            continue

        # Check if template matches deal configuration
        if template.matches(deal):
            selected_ids.append(template.template_id)
            seen_clause_keys.add(template.clause_key)

    # Ensure we have basic required clauses even if not explicitly matched
    # Add investment amount if missing
    if "investment_amount" not in seen_clause_keys:
        investment_template = next(
            (t for t in all_templates if t.template_id == "ts_investment_amount_v1"),
            None
        )
        if investment_template and investment_template.matches(deal):
            if "ts_investment_amount_v1" not in selected_ids:
                selected_ids.insert(0, "ts_investment_amount_v1")
                seen_clause_keys.add("investment_amount")

    # Add valuation if we have pre_money_valuation
    if deal.pre_money_valuation is not None and "pre_money_valuation" not in seen_clause_keys:
        valuation_template = next(
            (t for t in all_templates if t.template_id == "ts_valuation_v1"),
            None
        )
        if valuation_template and valuation_template.matches(deal):
            if "ts_valuation_v1" not in selected_ids:
                selected_ids.append("ts_valuation_v1")
                seen_clause_keys.add("pre_money_valuation")

    # Board seats handling is already done above during initial selection

    return selected_ids

