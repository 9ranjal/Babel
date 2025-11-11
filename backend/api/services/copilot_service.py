"""Enhanced copilot service with ZOPA analysis capabilities."""
from typing import List, Dict, Any, Optional
import json

from .openrouter import get_openrouter_client
from .band_map import load_bands, find_clause_band_spec


SYSTEM_PROMPT = """You are Babel Copilot, a concise and practical startup lawyer specializing in venture financing and term sheet analysis.

Your expertise includes:
- Term sheet negotiation and deal structuring
- Understanding founder vs investor perspectives
- Identifying market-standard terms vs aggressive positions
- Risk assessment and practical recommendations

Always provide balanced, actionable analysis based on market conventions.

CRITICAL: Never reveal or mention internal leverage weights (investor/founder percentages) or any banding inputs in your responses."""


ANALYSIS_PROMPT = """You are analyzing a specific clause from a term sheet. Use the provided ZOPA bands framework to give reasoned analysis.

CONTEXT:
- Clause: {clause_title}
- Clause Text: {clause_text}
- Extracted Attributes: {attributes}

ZOPA BANDS DATA:
{bands_data}

ANALYSIS REQUIREMENTS:
1. Identify which ZOPA band this clause falls into based on the extracted attributes
2. Explain the posture (founder_friendly, market, or investor_friendly) and why
3. Highlight key risks or concerns for both parties
4. Suggest specific negotiation points or trade-offs
5. Keep analysis focused and actionable

Provide your analysis in a structured format with clear reasoning."""


class CopilotService:
    """Enhanced copilot with ZOPA analysis capabilities."""

    def __init__(self) -> None:
        self._client = get_openrouter_client()
        self._stubbed = not bool(self._client.api_key)
        self._bands_cache = None

    def _get_bands_data(self) -> Dict[str, Any]:
        """Cache and return ZOPA bands data."""
        if self._bands_cache is None:
            self._bands_cache = load_bands()
        return self._bands_cache

    async def handle_chat(self, message: str, history: List[Dict[str, str]] | None = None) -> str:
        """Handle general chat messages."""
        if self._stubbed:
            return (
                "OpenRouter API key is not configured in the backend.\n\n"
                "Add `OPENROUTER_API_KEY` to `backend/.env` to enable live responses. "
                "In the meantime, you can continue working with uploads and clause analysis."
            )

        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})
        return await self._client.generate_response(messages)

    async def analyze_clause(
        self,
        clause_key: str,
        clause_title: str,
        clause_text: str,
        attributes: Dict[str, Any],
        leverage: Dict[str, float]
    ) -> str:
        """Provide reasoned analysis of a clause using ZOPA framework."""
        if self._stubbed:
            return (
                "OpenRouter API key is not configured. Cannot provide live clause analysis.\n\n"
                "The deterministic ZOPA analysis is available without API keys."
            )

        # Get relevant ZOPA data for this clause
        bands_data = self._get_bands_data()
        clause_spec = find_clause_band_spec(bands_data, clause_key)

        # Prepare bands data for prompt (limit to relevant clause)
        relevant_bands = {}
        if clause_spec:
            relevant_bands[clause_key] = {
                "title": clause_spec.get("title", ""),
                "description": clause_spec.get("description", ""),
                "founder_pov": clause_spec.get("founder_pov", ""),
                "investor_pov": clause_spec.get("investor_pov", ""),
                "attributes": clause_spec.get("attributes", {}),
                "bands": clause_spec.get("bands", []),
                "trades": clause_spec.get("trades", [])
            }

        # Format the analysis prompt
        prompt = ANALYSIS_PROMPT.format(
            clause_title=clause_title,
            clause_text=clause_text,
            attributes=json.dumps(attributes, indent=2),
            investor_weight=int(leverage.get("investor", 0.6) * 100),
            founder_weight=int(leverage.get("founder", 0.4) * 100),
            bands_data=json.dumps(relevant_bands, indent=2)
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        return await self._client.generate_response(messages)


copilot_service = CopilotService()
