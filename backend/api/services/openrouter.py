"""
OpenRouter client for conversational AI
"""
import httpx
from typing import Dict, Any, Optional
from ..core.settings import settings


class OpenRouterClient:
    """OpenRouter client for conversational AI"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL
        self.site_url = settings.OPENROUTER_SITE_URL
        self.app_name = settings.OPENROUTER_APP_NAME
    
    async def generate_response(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate response using OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            if response.status_code != 200:
                error_text = await response.aread()
                raise Exception(f"OpenRouter API error {response.status_code}: {error_text.decode()}")
            return response.json()["choices"][0]["message"]["content"]
    
    async def generate_intake_question(
        self,
        role: str,
        stage: str,
        region: str,
        previous_answers: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate dynamic intake question using OpenRouter"""
        
        # Build context from previous answers
        context = ""
        if previous_answers:
            context = f"Previous answers: {previous_answers}\n"
        
        system_prompt = f"""You are a term sheet negotiation expert conducting a {role} intake interview for a {stage} stage deal in {region}.

Your goal is to gather information to compute:
1. Leverage score (0-1): Based on runway, alternatives, repeat founder status
2. Clause weights: Which terms matter most to this {role}
3. BATNA (Best Alternative): Ideal values for each clause

Ask ONE targeted question that will help determine their negotiating position. Be conversational and specific to their situation.

Return JSON with:
- question_text: The question to ask
- question_type: "choice", "number", "text", or "boolean"
- options: Array of choices (if choice type)
- next_questions: Array of follow-up question IDs
- reasoning: Why this question matters for leverage/weights/BATNA

Focus on: {role} perspective, {stage} stage context, {region} market norms."""

        user_prompt = f"""Context: {context}
Generate the next intake question for this {role} in a {stage} deal."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.generate_response(messages, temperature=0.3)
            # Parse JSON response
            import json
            return json.loads(response)
        except Exception as e:
            # Fallback to static questions
            return self._get_fallback_question(role, stage)
    
    def _get_fallback_question(self, role: str, stage: str) -> Dict[str, Any]:
        """Fallback static questions if OpenRouter fails"""
        if role == "founder":
            return {
                "question_text": "What's your company's current runway in months?",
                "question_type": "number",
                "options": None,
                "next_questions": ["round_size", "alt_offers", "repeat_founder"],
                "reasoning": "Runway determines leverage - shorter runway = higher investor leverage"
            }
        else:
            return {
                "question_text": "What ownership percentage are you targeting?",
                "question_type": "number",
                "options": None,
                "next_questions": ["marquee", "fund_constraints", "diligence_speed"],
                "reasoning": "Ownership target affects negotiation weights and BATNA"
            }


def get_openrouter_client() -> OpenRouterClient:
    """Get OpenRouter client instance"""
    return OpenRouterClient()
