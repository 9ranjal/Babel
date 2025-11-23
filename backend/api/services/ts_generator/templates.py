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
                if isinstance(deal_value, (int, float)) and isinstance(value, (int, float)):
                    if abs(float(deal_value) - float(value)) > 0.001:
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
            template_text="""
    <tr>
      <th>Investment Amount and Investor Securities</th>
      <td>{investment_amount_formatted}</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall invest {currency} {investment_amount_formatted} into the Company through a primary investment at a pre-money valuation of {pre_money_valuation_formatted} through a mix of compulsorily convertible cumulative preference shares ("CCCPS"), and a nominal number of equity shares; such that the Investor will own atleast {ownership_percentage:.1f}% of the Company on a fully diluted post-money basis, post investment. If the total round size increases, the premoney valuation of the company would be adjusted accordingly to give the shareholding percentage above.
      </td>
    </tr>
""",
            required_fields=["investment_amount", "currency"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_valuation_v1",
            clause_key="pre_money_valuation",
            section_name="Economics",
            display_order=2,
            template_text="""
    <tr>
      <th>Pre-Money Valuation</th>
      <td>{pre_money_valuation_formatted}</td>
    </tr>
    <tr>
      <th>Post-Money Valuation</th>
      <td>{post_money_valuation_formatted}</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        Annexure A contains the proposed pre-money and post-money cap tables on a fully diluted basis.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Liquidity Preference</th>
      <td>{liquidation_preference_multiple:.0f}x, non-participating on defined liquidity events.</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The preference shares issued to the investor shall be in pari passu with other existing classes of preference shares. Liquidity Events in the definitive agreements shall include IPO, sale resulting in change of control, M&A, winding up of the Company etc.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Liquidity Preference</th>
      <td>{liquidation_preference_multiple:.0f}x, participating on defined liquidity events.</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The preference shares issued to the investor shall be in pari passu with other existing classes of preference shares. Liquidity Events in the definitive agreements shall include IPO, sale resulting in change of control, M&A, winding up of the Company etc.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Liquidity Preference</th>
      <td>{liquidation_preference_multiple:.0f}x, {liquidation_preference_participation_display.lower()} on defined liquidity events.</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The preference shares issued to the investor shall be in pari passu with other existing classes of preference shares. Liquidity Events in the definitive agreements shall include IPO, sale resulting in change of control, M&A, winding up of the Company etc.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Anti- Dilution Protection</th>
      <td>Broad-based weighted average</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall be entitled to anti-dilution protection on all future issuances at a price lower than the Investor's subscription price, on a broad-based weighted average basis.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Anti- Dilution Protection</th>
      <td>Narrow-based weighted average</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall be entitled to anti-dilution protection on all future issuances at a price lower than the Investor's subscription price, on a narrow-based weighted average basis.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Anti- Dilution Protection</th>
      <td>Full ratchet</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall be entitled to anti-dilution protection on all future issuances at a price lower than the Investor's subscription price, on a full ratchet basis.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>ESOP</th>
      <td>{option_pool_percent:.1f}%</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        An ESOP pool will be included in the {option_pool_timing}-money valuation, equal to {option_pool_percent:.1f}% of the share capital, on a post-money fully diluted basis.
      </td>
    </tr>
""",
            required_fields=["option_pool_percent", "option_pool_timing"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_preemptive_rights_v1",
            clause_key="preemptive_pro_rata",
            section_name="Ownership & Dilution",
            display_order=3,
            template_text="""
    <tr>
      <th>Pre-emptive Rights</th>
      <td>{preemptive_rights_scope_display}</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall have a right of first refusal to subscribe to its pro rata portion in any future fund raise.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Board of Directors</th>
      <td>{investor_board_seats} nominee director(s) and 1 observer</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall be entitled to appoint {investor_board_seats} nominee director(s) on the Board of the Company and 1 observer to attend all meetings of the Board in a non-voting capacity.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Board of Directors</th>
      <td>1 observer only</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall be entitled to appoint 1 observer to attend all meetings of the Board in a non-voting capacity.
      </td>
    </tr>
""",
            conditions={"investor_board_seats": 0},
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_observer_v1",
            clause_key="observer",
            section_name="Control & Governance",
            display_order=2,
            template_text="""
    <tr>
      <th>Board Observer Rights</th>
      <td>{observer_seats} observer seat(s)</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor shall be entitled to appoint {observer_seats} observer(s) to attend all meetings of the Board in a non-voting capacity.
      </td>
    </tr>
""",
            required_fields=["observer_seats"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_reserved_matters_v1",
            clause_key="reserved_matters",
            section_name="Control & Governance",
            display_order=3,
            template_text="""
    <tr>
      <th>Affirmative Rights</th>
      <td>{reserved_matters_scope_display}</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor will have affirmative consent rights (in relation to the Company and each subsidiary), including (but not limited to) in relation to the following: Economic rights such as approval rights on a change in the rights of securities, future fund-raise/ issue of capital, buy-backs/ redemption, dividends, etc; Governance rights such as approval rights on related party transactions, choice/change of auditors (Big 4 or any other mutually acceptable auditor), large expenses or debt obligations to be undertaken by the company, change in constitutional documents, significant litigation; and Change in control, M&A, trade sale, asset sale, disposition or acquisition of any subsidiaries, changes in business etc.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Investor's Right of First Refusal (ROFR)</th>
      <td>{rofr_days} days</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor will have a right of first refusal on any sale or transfer of shares held by the Founder(s) and all other shareholders of the Company.
      </td>
    </tr>
""",
            required_fields=["rofr_days"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_tag_along_v1",
            clause_key="tag_along",
            section_name="Transfer & Liquidity",
            display_order=2,
            template_text="""
    <tr>
      <th>Investor Tag Along Rights</th>
      <td>{tag_along_type_display}</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        Subject to the Investor's ROFR, the Investor will have the right to participate pro rata in any sale of shares to third parties by the Founder(s) or other shareholders, provided that if the Founder(s) shareholding will fall below a specified percentage pursuant to the transaction, the Investor may tag along up to its entire shareholding.
      </td>
    </tr>
""",
            required_fields=["tag_along_type"],
        )
    )

    templates.append(
        ClauseTemplate(
            template_id="ts_drag_along_v1",
            clause_key="drag_along",
            section_name="Transfer & Liquidity",
            display_order=3,
            template_text="""
    <tr>
      <th>Exit Rights</th>
      <td>{drag_along_years} years</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Company and the Founder(s) will provide an exit acceptable to the Investor through an IPO or trade sale, within a period of {drag_along_years} years ("Exit Period") from the date of closing of the investment. If the IPO is not completed within such time, the Investor shall have the right to require the Company and Founder(s) to provide an exit through sale to a third party buyer, or through a put, at fair market value (FMV). If such exit is also not completed within 6 months, the Investor shall have the right to drag all other shareholders to an exit.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Exclusivity</th>
      <td>{exclusivity_days} days</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Company agrees to negotiate the transaction contemplated above with the Investor on an exclusive basis for a period of {exclusivity_days} days from the signing of acceptance of this term sheet, or such other extended time as may be mutually agreed between the parties.
      </td>
    </tr>
""",
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
            template_text="""
    <tr>
      <th>Additional Rights</th>
      <td>Standard information and inspection rights</td>
    </tr>
    <tr>
      <td colspan="2" style="padding-top: 4px; padding-bottom: 8px;">
        The Investor will have all rights which any other existing or future investor (commensurate with the Investor's shareholding) in the Company may have. The Investor will also have standard information rights, including in relation to the receipt of audited and un-audited financial statements and quarterly MIS. In addition, Investors shall have standard inspection rights.
      </td>
    </tr>
""",
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

