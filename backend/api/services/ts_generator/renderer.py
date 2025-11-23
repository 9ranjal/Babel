"""Template rendering for term sheet generation."""
from __future__ import annotations

from typing import Dict, List

from ..build_graph import CATEGORY_TO_KEYS
from .templates import get_template_by_id, ClauseTemplate
from api.models.deal_schemas import DealConfig


def format_currency(value: float, currency: str = "USD") -> str:
    """Format currency value."""
    if currency == "USD":
        return f"${value:,.0f}"
    elif currency == "INR":
        return f"₹{value:,.0f}"
    else:
        return f"{currency} {value:,.0f}"


def get_liquidation_participation_description(participation: str) -> str:
    """Get description for liquidation preference participation."""
    if participation == "non_participating":
        return "After payment of the Liquidation Preference, the remaining assets of the Company shall be distributed pro rata to the holders of Common Stock."
    elif participation == "participating":
        return "After payment of the Liquidation Preference, the holders of Preferred Stock shall participate pro rata with the holders of Common Stock in the remaining assets of the Company."
    elif participation == "participating_with_cap":
        return "After payment of the Liquidation Preference, the holders of Preferred Stock shall participate pro rata with the holders of Common Stock in the remaining assets of the Company, provided that the total amount received per share of Preferred Stock shall not exceed a specified multiple of the Original Purchase Price."
    return ""


def get_preemptive_rights_description(scope: str) -> str:
    """Get description for preemptive rights scope."""
    if scope == "none":
        return "The Investors shall not have preemptive rights."
    elif scope == "limited_next_round":
        return "The Investors shall have the right to participate in the next round of financing only, on a pro rata basis."
    elif scope == "full_ongoing":
        return "The Investors shall have the right to participate pro rata in all future issuances of securities by the Company, subject to customary exceptions."
    return ""


def get_tag_along_description(tag_along_type: str) -> str:
    """Get description for tag-along rights."""
    if tag_along_type == "none":
        return "The Investors shall not have tag-along rights."
    elif tag_along_type == "pro_rata_only":
        return "If a Founder or major shareholder proposes to transfer shares representing more than a specified percentage of the Company, the Investors may participate in such transfer on a pro rata basis."
    elif tag_along_type == "full_on_threshold":
        return "The Investors shall have full tag-along rights on any transfer of shares by Founders or major shareholders above a specified threshold, allowing the Investors to sell a pro rata portion of their shares on the same terms."
    return ""


def get_reserved_matters_description(scope: str) -> str:
    """Get description for reserved matters scope."""
    if scope == "narrow_list":
        return "(i) amend the Company's charter or bylaws in a manner that adversely affects the rights of the Preferred Stock; (ii) increase or decrease the authorized number of shares of Preferred Stock; (iii) declare or pay dividends; (iv) liquidate, dissolve, or wind up the Company; (v) merge or consolidate with another entity; or (vi) sell all or substantially all of the Company's assets."
    elif scope == "market_list":
        return "(i) amend the Company's charter or bylaws in a manner that adversely affects the rights of the Preferred Stock; (ii) increase or decrease the authorized number of shares of any class of stock; (iii) declare or pay dividends; (iv) liquidate, dissolve, or wind up the Company; (v) merge or consolidate with another entity; (vi) sell all or substantially all of the Company's assets; (vii) incur indebtedness above a specified threshold; (viii) make material changes to the Company's business plan; or (ix) issue additional securities (other than pursuant to employee stock plans)."
    elif scope == "broad_list":
        return "In addition to the matters listed above, the Company shall also require Investor consent for: (x) any transaction with an affiliate; (xi) changes to the size or composition of the Board; (xii) material changes to compensation of executives; (xiii) entry into new lines of business; or (xiv) any other action that could materially affect the Investors' rights or the Company's value."
    return ""


def get_information_rights_description(level: str) -> str:
    """Get description for information rights level."""
    if level == "basic":
        return "(i) annual audited financial statements within 120 days of fiscal year end; (ii) quarterly unaudited financial statements within 45 days of quarter end; and (iii) annual budget within 30 days of the start of each fiscal year."
    elif level == "standard":
        return "(i) annual audited financial statements within 120 days of fiscal year end; (ii) quarterly unaudited financial statements within 45 days of quarter end; (iii) annual budget within 30 days of the start of each fiscal year; (iv) monthly unaudited financial statements within 30 days of month end; and (v) annual capitalization table."
    elif level == "comprehensive":
        return "In addition to the standard information rights, the Investors shall also receive: (vi) board meeting materials at least 48 hours in advance; (vii) access to key management for quarterly updates; (viii) notice of material events; (ix) inspection rights to visit the Company's facilities; and (x) such other information as reasonably requested."
    return ""


def render_term_sheet(deal: DealConfig, clause_ids: List[str]) -> str:
    """
    Render a term sheet from deal configuration and selected clause templates.
    
    Returns a Markdown-formatted term sheet.
    """
    # Group clauses by section
    sections: Dict[str, List[ClauseTemplate]] = {}
    for clause_id in clause_ids:
        template = get_template_by_id(clause_id)
        if template is None:
            continue

        section = template.section_name
        if section not in sections:
            sections[section] = []
        sections[section].append(template)

    # Sort templates within each section by display_order
    for section in sections:
        sections[section].sort(key=lambda t: t.display_order)

    # Build document
    lines: List[str] = []
    
    # Header
    lines.append(f"<h1>{deal.round_type} Term Sheet</h1>")
    lines.append("")
    lines.append("""<p>This indicative term sheet ("Term Sheet") summarizes the principal terms, for negotiation purposes only, with respect to a potential investment by [Insert Name of Investor] in [name of company]. Nothing herein creates any legally binding obligation on the part of any party, nor shall any legally binding obligations arise unless and until the parties have executed definitive written agreements (the "Definitive Agreements") and obtained all requisite governmental, corporate, management and legal approvals.</p>""")
    lines.append("")
    
    # Prepare context once for all templates
    context = {}
    for field_name in DealConfig.model_fields.keys():
        value = getattr(deal, field_name)
        context[field_name] = value

    # Format currency values
    currency = context.get("currency", "USD")
    currency_symbol = "USD" if currency == "USD" else "INR"
    for field in ["investment_amount", "pre_money_valuation", "post_money_valuation", "price_per_share"]:
        if field in context and context[field] is not None:
            context[f"{field}_formatted"] = format_currency(context[field], currency)
    
    # Calculate ownership percentage
    if context.get("investment_amount") and context.get("post_money_valuation"):
        ownership = (context["investment_amount"] / context["post_money_valuation"]) * 100
        context["ownership_percentage"] = ownership
    else:
        context["ownership_percentage"] = 0.0
    
    # Add descriptive text helpers
    if context.get("liquidation_preference_participation"):
        participation = context["liquidation_preference_participation"]
        context["liquidation_preference_participation_description"] = get_liquidation_participation_description(participation)
        if participation == "non_participating":
            context["liquidation_preference_participation_display"] = "Non-participating"
        elif participation == "participating":
            context["liquidation_preference_participation_display"] = "Participating"
        elif participation == "participating_with_cap":
            context["liquidation_preference_participation_display"] = "Participating with cap"
        else:
            context["liquidation_preference_participation_display"] = participation.replace("_", " ").title()
    if context.get("preemptive_rights_scope"):
        scope = context["preemptive_rights_scope"]
        context["preemptive_rights_description"] = get_preemptive_rights_description(scope)
        if scope == "none":
            context["preemptive_rights_scope_display"] = "None"
        elif scope == "limited_next_round":
            context["preemptive_rights_scope_display"] = "Limited to next round"
        elif scope == "full_ongoing":
            context["preemptive_rights_scope_display"] = "Full ongoing"
        else:
            context["preemptive_rights_scope_display"] = scope.replace("_", " ").title()
    if context.get("tag_along_type"):
        context["tag_along_description"] = get_tag_along_description(context["tag_along_type"])
        tag_along = context["tag_along_type"]
        if tag_along == "none":
            context["tag_along_type_display"] = "None"
        elif tag_along == "pro_rata_only":
            context["tag_along_type_display"] = "Pro rata only"
        elif tag_along == "full_on_threshold":
            context["tag_along_type_display"] = "Full on threshold"
        else:
            context["tag_along_type_display"] = tag_along.replace("_", " ").title()
    if context.get("reserved_matters_scope"):
        context["reserved_matters_description"] = get_reserved_matters_description(context["reserved_matters_scope"])
        scope = context["reserved_matters_scope"]
        if scope == "narrow_list":
            context["reserved_matters_scope_display"] = "Narrow list"
        elif scope == "market_list":
            context["reserved_matters_scope_display"] = "Market list"
        elif scope == "broad_list":
            context["reserved_matters_scope_display"] = "Broad list"
        else:
            context["reserved_matters_scope_display"] = scope.replace("_", " ").title()
    if context.get("information_rights_level"):
        context["information_rights_description"] = get_information_rights_description(context["information_rights_level"])
        level = context["information_rights_level"]
        if level == "basic":
            context["information_rights_level_display"] = "Basic"
        elif level == "standard":
            context["information_rights_level_display"] = "Standard"
        elif level == "comprehensive":
            context["information_rights_level_display"] = "Comprehensive"
        else:
            context["information_rights_level_display"] = level.replace("_", " ").title()
    
    # Board composition helpers
    board_size = context.get("board_size")
    if board_size is None:
        investor_seats = context.get("investor_board_seats", 0) or 0
        founder_seats = context.get("founder_board_seats") or 0
        independent_seats = context.get("independent_board_seats") or 0
        board_size = investor_seats + founder_seats + independent_seats
    context["board_size_display"] = board_size if board_size else "such number as determined by the parties"
    founder_seats = context.get("founder_board_seats")
    context["founder_board_seats_display"] = str(founder_seats) if founder_seats else "None"
    independent_seats = context.get("independent_board_seats")
    context["independent_board_seats_display"] = str(independent_seats) if independent_seats else "None"

    # Start main table
    lines.append('<table class="ts-table">')
    lines.append("  <tbody>")

    # Render sections in category order (from CATEGORY_TO_KEYS)
    category_order = list(CATEGORY_TO_KEYS.keys())
    rendered_sections = set()
    
    for category in category_order:
        if category not in sections:
            continue
        rendered_sections.add(category)

        # Render clauses in this section as table rows
        for template in sections[category]:
            try:
                rendered = template.template_text.format(**context)
                # Extract table rows from the rendered template (remove table/tbody wrappers)
                import re
                # Remove table and tbody tags, keep only tr elements
                rendered = re.sub(r'<table[^>]*>', '', rendered)
                rendered = re.sub(r'</table>', '', rendered)
                rendered = re.sub(r'<tbody[^>]*>', '', rendered)
                rendered = re.sub(r'</tbody>', '', rendered)
                # Extract all tr elements
                row_matches = re.findall(r'<tr>(.*?)</tr>', rendered, re.DOTALL)
                for row_html in row_matches:
                    lines.append(f"    <tr>{row_html}</tr>")
            except (KeyError, ValueError) as e:
                continue
    
    # Render any remaining sections
    remaining_sections = sorted(set(sections.keys()) - rendered_sections)
    for section in remaining_sections:
        for template in sections[section]:
            try:
                rendered = template.template_text.format(**context)
                import re
                rendered = re.sub(r'<table[^>]*>', '', rendered)
                rendered = re.sub(r'</table>', '', rendered)
                rendered = re.sub(r'<tbody[^>]*>', '', rendered)
                rendered = re.sub(r'</tbody>', '', rendered)
                row_matches = re.findall(r'<tr>(.*?)</tr>', rendered, re.DOTALL)
                for row_html in row_matches:
                    lines.append(f"    <tr>{row_html}</tr>")
            except (KeyError, ValueError):
                continue
    
    # Close table
    lines.append("  </tbody>")
    lines.append("</table>")
    lines.append("")
    lines.append("<p><em>This term sheet is generated automatically. Please review with legal counsel.</em></p>")

    return "\n".join(lines)

