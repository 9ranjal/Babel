"""Clause templates for term sheet generation."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ClauseTemplate:
    """Represents a clause template for term sheet generation."""

    def __init__(
        self,
        template_id: str,
        clause_key: str,
        section_name: str,
        display_order: int,
        template_text: str,
        conditions: Optional[Dict[str, Any]] = None,
        required_fields: Optional[List[str]] = None,
    ):
        self.template_id = template_id
        self.clause_key = clause_key
        self.section_name = section_name
        self.display_order = display_order
        self.template_text = template_text
        self.conditions = conditions or {}
        self.required_fields = required_fields or []

    def matches(self, deal: Any) -> bool:
        """Check if this template matches the deal configuration."""
        # Check required fields
        for field in self.required_fields:
            if not hasattr(deal, field):
                return False
            field_value = getattr(deal, field)
            if field_value is None:
                return False

        # Check conditions
        for key, value in self.conditions.items():
            if not hasattr(deal, key):
                return False
            deal_value = getattr(deal, key)
            if isinstance(value, list):
                # Enum match: value must be in list
                if deal_value not in value:
                    return False
            elif isinstance(value, str) and value == "not_null":
                # Field must not be null
                if deal_value is None:
                    return False
            elif isinstance(value, (int, float)):
                # Exact numeric match (with tolerance for floats)
                if isinstance(deal_value, float) and isinstance(value, float):
                    if abs(deal_value - value) > 0.001:
                        return False
                elif deal_value != value:
                    return False
            elif isinstance(value, str):
                # Exact string match
                if deal_value != value:
                    return False

        return True


def get_clause_templates() -> List[ClauseTemplate]:
    """Return all available clause templates."""
    templates = []

    # Economics section
    templates.append(
        ClauseTemplate(
            template_id="ts_investment_amount_v1",
            clause_key="investment_amount",
            section_name="Economics",
            display_order=1,
            template_text="**Investment Amount:** {investment_amount_formatted}",
            required_fields=["investment_amount", "currency"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_valuation_v1",
            clause_key="pre_money_valuation",
            section_name="Economics",
            display_order=2,
            template_text="**Pre-Money Valuation:** {pre_money_valuation_formatted}\n**Post-Money Valuation:** {post_money_valuation_formatted}",
            required_fields=["pre_money_valuation", "post_money_valuation"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_securities_v1",
            clause_key="securities",
            section_name="Economics",
            display_order=3,
            template_text="**Securities:** {securities}",
            required_fields=["securities"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_liqpref_1x_np_v1",
            clause_key="liquidation_preference",
            section_name="Economics",
            display_order=4,
            template_text="**Liquidation Preference:** {liquidation_preference_multiple:.1f}x, non-participating",
            conditions={"liquidation_preference_multiple": 1.0, "liquidation_preference_participation": "non_participating"},
            required_fields=["liquidation_preference_multiple"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_liqpref_1x_p_v1",
            clause_key="liquidation_preference",
            section_name="Economics",
            display_order=4,
            template_text="**Liquidation Preference:** {liquidation_preference_multiple:.1f}x, participating",
            conditions={"liquidation_preference_multiple": 1.0, "liquidation_preference_participation": "participating"},
            required_fields=["liquidation_preference_multiple"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_liqpref_custom_v1",
            clause_key="liquidation_preference",
            section_name="Economics",
            display_order=4,
            template_text="**Liquidation Preference:** {liquidation_preference_multiple:.1f}x, {liquidation_preference_participation}",
            conditions={"liquidation_preference_multiple": "not_null", "liquidation_preference_participation": "not_null"},
            required_fields=["liquidation_preference_multiple", "liquidation_preference_participation"],
        )
    )

    # Ownership & Dilution section
    templates.append(
        ClauseTemplate(
            template_id="ts_anti_dilution_broad_wa_v1",
            clause_key="anti_dilution",
            section_name="Ownership & Dilution",
            display_order=1,
            template_text="**Anti-Dilution:** Broad-based weighted average",
            conditions={"anti_dilution_type": "broad_wa"},
            required_fields=["anti_dilution_type"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_anti_dilution_narrow_wa_v1",
            clause_key="anti_dilution",
            section_name="Ownership & Dilution",
            display_order=1,
            template_text="**Anti-Dilution:** Narrow-based weighted average",
            conditions={"anti_dilution_type": "narrow_wa"},
            required_fields=["anti_dilution_type"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_anti_dilution_full_ratchet_v1",
            clause_key="anti_dilution",
            section_name="Ownership & Dilution",
            display_order=1,
            template_text="**Anti-Dilution:** Full ratchet",
            conditions={"anti_dilution_type": "full_ratchet"},
            required_fields=["anti_dilution_type"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_option_pool_v1",
            clause_key="option_pool",
            section_name="Ownership & Dilution",
            display_order=2,
            template_text="**Option Pool:** {option_pool_percent:.1f}% ({option_pool_timing}-money)",
            required_fields=["option_pool_percent", "option_pool_timing"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_preemptive_rights_v1",
            clause_key="preemptive_pro_rata",
            section_name="Ownership & Dilution",
            display_order=3,
            template_text="**Pre-emptive Rights:** {preemptive_rights_scope}",
            required_fields=["preemptive_rights_scope"],
        )
    )

    # Control & Governance section
    templates.append(
        ClauseTemplate(
            template_id="ts_board_composition_v1",
            clause_key="board",
            section_name="Control & Governance",
            display_order=1,
            template_text="**Board Composition:**\n- Investor Directors: {investor_board_seats}\n- Founder Directors: {founder_board_seats}\n- Independent Directors: {independent_board_seats}",
            conditions={"investor_board_seats": "not_null"},
            required_fields=["investor_board_seats"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_board_no_seats_v1",
            clause_key="board",
            section_name="Control & Governance",
            display_order=1,
            template_text="**Board Composition:** No investor board seats",
            conditions={"investor_board_seats": 0},
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_observer_v1",
            clause_key="observer",
            section_name="Control & Governance",
            display_order=2,
            template_text="**Board Observer:** {observer_seats} observer seat(s)",
            required_fields=["observer_seats"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_reserved_matters_v1",
            clause_key="reserved_matters",
            section_name="Control & Governance",
            display_order=3,
            template_text="**Reserved Matters:** {reserved_matters_scope}",
            required_fields=["reserved_matters_scope"],
        )
    )

    # Transfer & Liquidity section
    templates.append(
        ClauseTemplate(
            template_id="ts_rofr_v1",
            clause_key="rofr",
            section_name="Transfer & Liquidity",
            display_order=1,
            template_text="**Right of First Refusal:** {rofr_days} days",
            required_fields=["rofr_days"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_tag_along_v1",
            clause_key="tag_along",
            section_name="Transfer & Liquidity",
            display_order=2,
            template_text="**Tag-Along Rights:** {tag_along_type}",
            required_fields=["tag_along_type"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_drag_along_v1",
            clause_key="drag_along",
            section_name="Transfer & Liquidity",
            display_order=3,
            template_text="**Drag-Along Rights:** {drag_along_years} years",
            required_fields=["drag_along_years"],
        )
    )

    # Deal Process & Closing section
    templates.append(
        ClauseTemplate(
            template_id="ts_exclusivity_v1",
            clause_key="exclusivity",
            section_name="Deal Process & Closing",
            display_order=1,
            template_text="**Exclusivity:** {exclusivity_days} days",
            required_fields=["exclusivity_days"],
        )
    )

    # Information & Oversight section
    templates.append(
        ClauseTemplate(
            template_id="ts_information_rights_v1",
            clause_key="information_rights",
            section_name="Information & Oversight",
            display_order=1,
            template_text="**Information Rights:** {information_rights_level}",
            required_fields=["information_rights_level"],
        )
    )

    return templates


def get_template_by_id(template_id: str) -> Optional[ClauseTemplate]:
    """Get a template by its ID."""
    for template in get_clause_templates():
        if template.template_id == template_id:
            return template
    return None

