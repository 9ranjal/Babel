"""Template rendering for term sheet generation."""
from __future__ import annotations

from typing import Dict, List

from ..build_graph import CATEGORY_TO_KEYS
from .templates import get_template_by_id
from api.models.deal_schemas import DealConfig


def format_currency(value: float, currency: str = "USD") -> str:
    """Format currency value."""
    if currency == "USD":
        return f"${value:,.0f}"
    elif currency == "INR":
        return f"₹{value:,.0f}"
    else:
        return f"{currency} {value:,.0f}"


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
    lines.append("# Term Sheet")
    lines.append("")
    lines.append(f"**Round:** {deal.round_type}")
    lines.append(f"**Instrument:** {deal.instrument_type}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Render sections in category order (from CATEGORY_TO_KEYS)
    category_order = list(CATEGORY_TO_KEYS.keys())
    
    # Track which sections we've rendered
    rendered_sections = set()
    
    for category in category_order:
        if category not in sections:
            continue
        rendered_sections.add(category)

        # Section heading
        lines.append(f"## {category}")
        lines.append("")

        # Render clauses in this section
        for template in sections[category]:
            # Prepare template context from deal
            context = {}
            for field_name in deal.model_fields.keys():
                value = getattr(deal, field_name)
                context[field_name] = value

            # Format currency values for template placeholders
            currency = context.get("currency", "USD")
            for field in ["investment_amount", "pre_money_valuation", "post_money_valuation", "price_per_share"]:
                if field in context and context[field] is not None:
                    context[f"{field}_formatted"] = format_currency(context[field], currency)

            # Render template
            try:
                rendered = template.template_text.format(**context)
                lines.append(rendered)
                lines.append("")
            except (KeyError, ValueError) as e:
                # Skip if template has missing placeholders
                continue

        lines.append("")
    
    # Render any remaining sections not in CATEGORY_TO_KEYS (sorted alphabetically)
    remaining_sections = sorted(set(sections.keys()) - rendered_sections)
    for section in remaining_sections:
        lines.append(f"## {section}")
        lines.append("")
        
        for template in sections[section]:
            context = {}
            for field_name in deal.model_fields.keys():
                value = getattr(deal, field_name)
                context[field_name] = value

            currency = context.get("currency", "USD")
            for field in ["investment_amount", "pre_money_valuation", "post_money_valuation", "price_per_share"]:
                if field in context and context[field] is not None:
                    context[f"{field}_formatted"] = format_currency(context[field], currency)

            try:
                rendered = template.template_text.format(**context)
                lines.append(rendered)
                lines.append("")
            except (KeyError, ValueError):
                continue

        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This term sheet is generated automatically. Please review with legal counsel.*")

    return "\n".join(lines)

