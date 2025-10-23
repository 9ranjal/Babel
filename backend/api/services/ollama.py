"""
Ollama client for local LLM inference
"""
import httpx
from typing import Dict, Any, Optional
import json


class OllamaClient:
    """Ollama client for local LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen2.5:3b-instruct-q4_0"  # Default model, can be overridden
    
    async def generate_response(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = None
    ) -> str:
        """Generate response using Ollama"""
        model = model or self.model
        
        # Convert messages to Ollama format
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60.0
            )
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"Ollama API error {response.status_code}: {error_text}")
            
            result = response.json()
            return result["response"]
    
    def _messages_to_prompt(self, messages: list[Dict[str, str]]) -> str:
        """Convert chat messages to Ollama prompt format"""
        prompt_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"
    
    async def generate_intake_question(
        self,
        role: str,
        stage: str,
        region: str,
        previous_answers: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate dynamic intake question using Ollama"""
        
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
            response = await self.generate_response(messages, temperature=0.7)
            # Try to extract JSON from response
            response_text = response.strip()
            
            # Look for JSON in the response
            if "{" in response_text and "}" in response_text:
                # Extract JSON part
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # If no JSON found, create a structured response
                return {
                    "question_text": response_text,
                    "question_type": "text",
                    "options": None,
                    "next_questions": ["follow_up"],
                    "reasoning": "AI generated question"
                }
        except Exception as e:
            # Fallback to static questions
            return self._get_fallback_question(role, stage)
    
    def _get_fallback_question(self, role: str, stage: str) -> Dict[str, Any]:
        """Fallback static questions if Ollama fails"""
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


def get_ollama_client() -> OllamaClient:
    """Get Ollama client instance"""
    return OllamaClient()
