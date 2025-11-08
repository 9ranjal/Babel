"""Minimal copilot service that proxies to OpenRouter."""
from typing import List, Dict

from .openrouter import get_openrouter_client


SYSTEM_PROMPT = """You are Babel Copilot, a concise and practical startup lawyer.
Offer clear, actionable guidance for venture financing and negotiation questions.
Use plain language, highlight risks, and keep responses under 6 paragraphs."""


class CopilotService:
    """Lightweight wrapper around the OpenRouter client."""

    def __init__(self) -> None:
        self._client = get_openrouter_client()
        self._stubbed = not bool(self._client.api_key)

    async def handle_chat(self, message: str, history: List[Dict[str, str]] | None = None) -> str:
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


copilot_service = CopilotService()
