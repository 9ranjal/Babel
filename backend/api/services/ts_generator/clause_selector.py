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

    # Iterate through templates and select matching ones
    for template in all_templates:
        # Skip if we've already selected a template for this clause_key
        if template.clause_key in seen_clause_keys:
            continue

        # Skip SAFE-excluded clauses
        if template.clause_key in safe_excluded_clause_keys:
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

    # If investor_board_seats is 0, ensure we use the "no seats" template
    if deal.investor_board_seats == 0:
        # Remove any board composition template
        selected_ids = [
            tid for tid in selected_ids
            if not any(
                template.template_id == tid and template.clause_key == "board" and template.template_id != "ts_board_no_seats_v1"
                for template in all_templates
            )
        ]
        # Add no seats template if not present
        if "board" not in seen_clause_keys:
            no_seats_template = next(
                (t for t in all_templates if t.template_id == "ts_board_no_seats_v1"),
                None
            )
            if no_seats_template:
                selected_ids.append("ts_board_no_seats_v1")
                seen_clause_keys.add("board")

    return selected_ids

