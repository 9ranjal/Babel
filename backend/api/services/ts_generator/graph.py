"""LangGraph workflow for term sheet generation."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from api.models.deal_schemas import DealConfig, DealOverrides, get_base_deal_config
from .clause_selector import select_clause_templates
from .renderer import render_term_sheet
from .base_template import get_base_template_text
from ..openrouter import get_openrouter_client


class DealState(TypedDict):
    """State for the term sheet generation graph."""
    nl_input: str
    overrides: Optional[DealOverrides]
    deal: Optional[DealConfig]
    validation_errors: List[str]
    selected_clause_ids: List[str]
    rendered_term_sheet: Optional[str]
    clarification_questions: Optional[List[str]]


def input_node(state: DealState) -> DealState:
    """Initialize state with NL input."""
    return state


async def parse_nl_node(state: DealState) -> DealState:
    """Parse natural language input into DealOverrides using LLM."""
    nl_input = state["nl_input"]
    client = get_openrouter_client()

    # Create prompt for LLM to extract deal terms
    prompt = f"""Extract deal terms from the following natural language description and return as JSON matching this schema:

{{
  "investment_amount": float (optional),
  "pre_money_valuation": float (optional),
  "post_money_valuation": float (optional),
  "currency": str (optional, default "USD"),
  "round_type": str (optional, e.g., "Seed", "Series A"),
  "instrument_type": str (optional, e.g., "CCPS", "SAFE", "Equity"),
  "investor_board_seats": int (optional),
  "observer_seats": int (optional),
  "option_pool_percent": float (optional),
  "option_pool_timing": str (optional, "pre" or "post"),
  "liquidation_preference_multiple": float (optional),
  "liquidation_preference_participation": str (optional, "non_participating", "participating", "participating_with_cap"),
  "anti_dilution_type": str (optional, "none", "broad_wa", "narrow_wa", "full_ratchet"),
  "exclusivity_days": int (optional),
  "rofr_days": int (optional),
  "tag_along_type": str (optional, "none", "pro_rata_only", "full_on_threshold"),
  "drag_along_years": int (optional),
  "reserved_matters_scope": str (optional, "narrow_list", "market_list", "broad_list"),
  "preemptive_rights_scope": str (optional, "none", "limited_next_round", "full_ongoing"),
  "information_rights_level": str (optional)
}}

NUMERIC FORMATTING RULES:
- "5M" or "5 m" or "5 million" = 5000000
- "10M" or "10 million" = 10000000
- "2.5M" or "2.5 million" = 2500000
- "5 crore" or "5 cr" = 50000000
- "50 lakh" or "50L" = 5000000
- "1K" or "1k" or "1 thousand" = 1000
- "25" by itself in context of valuation = 25000000 (if "25 premoney" means 25M)

CURRENCY DETECTION:
- "₹" or "INR" or "rupees" → currency = "INR"
- "$" or "USD" or "dollars" → currency = "USD"
- If no currency specified, default to "USD"

VALUATION CLARITY:
- "25 premoney" or "25 pre-money" → pre_money_valuation = 25000000 (assuming millions)
- "25 postmoney" or "25 post-money" → post_money_valuation = 25000000
- If user does not specify "pre" vs "post", do NOT invent - leave the field null
- "at 25" without context → leave null (ambiguous)

Natural language input: "{nl_input}"

Return ONLY valid JSON, no other text. Extract only fields explicitly mentioned in the input. If a field is not mentioned, omit it from the JSON."""

    messages = [
        {
            "role": "system",
            "content": "You are a term sheet parser. Extract structured deal terms from natural language. Return only valid JSON.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = await client.generate_response(messages, temperature=0.0, max_tokens=2000)
        # Parse JSON from response
        # Try to extract JSON if response has extra text
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        overrides_dict = json.loads(response)
        overrides = DealOverrides(**overrides_dict)
    except Exception as e:
        # Fallback: create empty overrides if parsing fails
        overrides = DealOverrides()

    return {**state, "overrides": overrides}


def apply_defaults_node(state: DealState) -> DealState:
    """Merge overrides with base deal config defaults."""
    base_config = get_base_deal_config()
    overrides = state.get("overrides")

    if overrides is None:
        deal = base_config
    else:
        # Merge overrides into base config
        # Use model_dump(exclude_unset=True) to only get fields that were explicitly set
        overrides_dict = overrides.model_dump(exclude_unset=True, exclude_none=False)
        deal_dict = base_config.model_dump()
        # Update base config with overrides (overrides take precedence)
        deal_dict.update(overrides_dict)
        deal = DealConfig(**deal_dict)

    return {**state, "deal": deal}


def validate_deal_node(state: DealState) -> DealState:
    """Validate deal configuration."""
    deal = state.get("deal")
    errors: List[str] = []
    questions: List[str] = []

    if deal is None:
        errors.append("Deal configuration is missing")
        return {**state, "validation_errors": errors, "clarification_questions": questions}

    # Check critical fields
    if deal.investment_amount <= 0:
        errors.append("Investment amount must be greater than 0")
        questions.append("What is the investment amount?")

    if deal.pre_money_valuation is None and deal.instrument_type != "SAFE":
        errors.append("Pre-money valuation is required for non-SAFE instruments")
        questions.append("What is the pre-money valuation?")

    # Check post-money consistency
    if deal.pre_money_valuation is not None and deal.post_money_valuation is not None:
        expected_post = deal.pre_money_valuation + deal.investment_amount
        if abs(deal.post_money_valuation - expected_post) > 0.01:
            errors.append(
                f"Post-money valuation ({deal.post_money_valuation}) does not match "
                f"pre-money ({deal.pre_money_valuation}) + investment ({deal.investment_amount})"
            )

    # SAFE-specific validation
    # In v0, we allow SAFE without explicit valuation cap

    return {**state, "validation_errors": errors, "clarification_questions": questions}


def should_continue(state: DealState) -> str:
    """Determine if we should continue (always continue for v0)."""
    # In v0, we always continue even with validation errors
    # Errors are returned in the response but don't block generation
    return "continue"


def select_ts_clauses_node(state: DealState) -> DealState:
    """Select clause templates based on deal configuration."""
    deal = state.get("deal")
    if deal is None:
        return {**state, "selected_clause_ids": []}

    clause_ids = select_clause_templates(deal)
    return {**state, "selected_clause_ids": clause_ids}


async def render_ts_node(state: DealState) -> DealState:
    """Render term sheet using base template as reference, modified by deal config."""
    deal = state.get("deal")
    clause_ids = state.get("selected_clause_ids", [])

    if deal is None:
        return {**state, "rendered_term_sheet": None}

    # Get base template text
    base_template = get_base_template_text()
    
    # Use LLM to modify base template based on deal config
    client = get_openrouter_client()
    
    # Convert deal config to JSON for LLM
    deal_dict = deal.model_dump(exclude_none=True)
    deal_json = json.dumps(deal_dict, indent=2)
    
    prompt = f"""You are a term sheet generator. You have a base term sheet template and a deal configuration.

BASE TEMPLATE:
{base_template}

DEAL CONFIGURATION (JSON):
{deal_json}

TASK:
Generate a complete term sheet by modifying the base template according to the deal configuration. 
- Replace placeholder values (like [Insert Investment Amount]) with actual values from the deal configuration
- Keep the exact language, structure, and formatting of the base template
- Maintain the two-column table format (Label | Value)
- For each term, include the label in the left column and the value in the right column
- Add descriptive paragraphs below terms when appropriate, spanning both columns
- Use the exact legal language from the base template, only updating the specific values
- Format currency values appropriately (e.g., $5,000,000 for USD, ₹5,00,000 for INR)
- Return the complete term sheet in HTML format with proper table structure

Return ONLY the HTML term sheet, no other text."""

    messages = [
        {
            "role": "system",
            "content": "You are a legal document generator specializing in term sheets. You modify base templates with deal-specific values while preserving the original legal language and structure.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        rendered = await client.generate_response(messages, temperature=0.0, max_tokens=4000)
        # Clean up response
        rendered = rendered.strip()
        if rendered.startswith("```html"):
            rendered = rendered[7:]
        if rendered.startswith("```"):
            rendered = rendered[3:]
        if rendered.endswith("```"):
            rendered = rendered[:-3]
        rendered = rendered.strip()
    except Exception:
        # Fallback to template-based rendering if LLM fails
        rendered = render_term_sheet(deal, clause_ids)
    
    return {**state, "rendered_term_sheet": rendered}


def output_node(state: DealState) -> DealState:
    """Prepare final output."""
    return state


def create_term_sheet_graph() -> StateGraph:
    """Create and configure the term sheet generation graph."""
    workflow = StateGraph(DealState)

    # Add nodes
    workflow.add_node("input", input_node)
    workflow.add_node("parse_nl", parse_nl_node)
    workflow.add_node("apply_defaults", apply_defaults_node)
    workflow.add_node("validate_deal", validate_deal_node)
    workflow.add_node("select_clauses", select_ts_clauses_node)
    workflow.add_node("render_ts", render_ts_node)
    workflow.add_node("output", output_node)

    # Set entry point
    workflow.set_entry_point("input")

    # Add edges
    workflow.add_edge("input", "parse_nl")
    workflow.add_edge("parse_nl", "apply_defaults")
    workflow.add_edge("apply_defaults", "validate_deal")
    workflow.add_conditional_edges(
        "validate_deal",
        should_continue,
        {
            "continue": "select_clauses",
        },
    )
    workflow.add_edge("select_clauses", "render_ts")
    workflow.add_edge("render_ts", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


# Global graph instance
_graph = None


def get_graph():
    """Get or create the term sheet generation graph."""
    global _graph
    if _graph is None:
        _graph = create_term_sheet_graph()
    return _graph


def reset_graph():
    """Reset the graph instance (useful for testing)."""
    global _graph
    _graph = None


async def generate_term_sheet(nl_input: str) -> Dict[str, Any]:
    """
    Generate a term sheet from natural language input.
    
    Returns a dictionary with:
    - term_sheet: str (Markdown formatted term sheet)
    - deal_config: dict (structured deal configuration)
    - validation_errors: List[str] (any validation warnings)
    """
    graph = get_graph()

    initial_state: DealState = {
        "nl_input": nl_input,
        "overrides": None,
        "deal": None,
        "validation_errors": [],
        "selected_clause_ids": [],
        "rendered_term_sheet": None,
        "clarification_questions": None,
    }

    # Run graph
    final_state = await graph.ainvoke(initial_state)

    return {
        "term_sheet": final_state.get("rendered_term_sheet", ""),
        "deal_config": final_state.get("deal").model_dump() if final_state.get("deal") else {},
        "validation_errors": final_state.get("validation_errors", []),
        "clarification_questions": final_state.get("clarification_questions", []),
    }

