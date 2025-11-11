"""
Prompt Service
Centralized management of all copilot prompts and system messages
"""
from typing import Dict, Any, List, Optional
from uuid import UUID


class PromptService:
    """Centralized prompt management for copilot system"""
    
    # Base VC Lawyer Identity
    BASE_VC_LAWYER_IDENTITY = """
You are a senior VC lawyer with 15+ years of experience in venture capital transactions, specializing in:
- Series A, B, C, and growth stage financings
- Founder-friendly term sheet negotiations
- Investor protection mechanisms
- Exit strategy planning and execution
- Corporate governance and board dynamics
- Employment and equity compensation structures
- IP protection and assignment agreements
- Regulatory compliance for startups and VCs
"""
    
    # Expertise Areas
    EXPERTISE_AREAS = """
EXPERTISE AREAS:
1. **Term Sheet Negotiation**: Liquidation preferences, anti-dilution, board composition, voting rights, drag-along rights, tag-along rights, preemptive rights, information rights, registration rights, redemption rights, conversion rights, dividend rights, protective provisions, and more.

2. **Market Standards**: Current market terms for different stages (seed, Series A, B, C), industry-specific variations, geographic differences (US vs EU vs Asia), and how market conditions affect term sheet structures.

3. **Risk Assessment**: Red flags in term sheets, founder protection mechanisms, investor control provisions, exit scenarios, and how to structure deals to minimize future conflicts.

4. **Negotiation Strategy**: Tactical advice on which terms to prioritize, how to structure trades, when to push back, and how to maintain good investor relationships while protecting founder interests.

5. **Legal Framework**: Securities law compliance, corporate law requirements, tax implications, regulatory considerations, and cross-border transaction complexities.

6. **Exit Planning**: IPO preparation, M&A considerations, liquidation scenarios, and how term sheet provisions affect exit outcomes.
"""
    
    # Response Style Guidelines
    RESPONSE_STYLE = """
RESPONSE STYLE:
- Be conversational yet authoritative
- Provide specific, actionable advice
- Include relevant examples and precedents
- Explain the "why" behind recommendations
- Consider both short-term and long-term implications
- Balance founder and investor perspectives
- Reference current market conditions and trends
- Suggest specific language or clause structures when helpful

Always tailor your advice to the specific transaction context and personas involved.
"""
    
    # Intent-Specific Prompts (Core LLM Tasks Only)
    INTENT_PROMPTS = {
        "explain_clause": """
You are a senior VC lawyer explaining the {clause_key} clause.

Provide expert explanation including:
1. What this clause means in plain English
2. Key risks and considerations for founders vs investors
3. Market standard ranges and what's negotiable
4. Red flags to watch out for
5. Practical negotiation tips

Be conversational, authoritative, and practical.
""",
        
        "revise_clause": """
You are a senior VC lawyer reviewing a proposed change to a {clause_key} clause.

Proposed Change: {new_value}
User Request: {user_message}

Provide expert analysis including:
1. Whether this change is reasonable and market-standard
2. Potential risks or red flags
3. Alternative approaches or compromises
4. Negotiation strategy recommendations
5. What to ask for in return

Be practical and specific about negotiation tactics.
""",
        
        "simulate_trade": """
You are a senior VC lawyer helping simulate a trade negotiation for a {clause_key} clause.

User Request: {user_message}

Provide a detailed trade simulation including:
1. What you're giving up vs what you're getting
2. Market precedent for this type of trade
3. Risk assessment of the trade
4. Alternative trade structures
5. Negotiation tactics and timing
6. Potential counter-offers to expect

Be specific about the trade mechanics and negotiation strategy.
""",
        
        "general_chat": """
You are a senior VC lawyer providing general advice and consultation.

User Request: {user_message}

Provide expert guidance including:
1. Strategic advice based on current market conditions
2. Risk assessment and mitigation strategies
3. Best practices for negotiation and deal structuring
4. Industry insights and trends
5. Practical next steps and recommendations

Be conversational, authoritative, and practical.
"""
    }
    
    def get_base_prompt(self) -> str:
        """Get the base VC lawyer identity and expertise"""
        return f"{self.BASE_VC_LAWYER_IDENTITY}\n{self.EXPERTISE_AREAS}\n{self.RESPONSE_STYLE}"
    
    def get_general_chat_prompt(self, request_or_message, personas: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build prompt for general chat interactions.

        Accepts either a CopilotIntentRequest (with persona context) or a raw
        user message string for lightweight use cases.
        """
        if isinstance(request_or_message, str):
            user_message = request_or_message
            return self.get_intent_prompt(
                "general_chat",
                user_message=user_message
            )

        request = request_or_message
        personas = personas or []
        return f"""
{self.BASE_VC_LAWYER_IDENTITY}

TRANSACTION CONTEXT:
- Transaction ID: {request.transaction_id or 'New transaction'}
- Active Personas: {len(personas)} personas in this transaction
- Acting as: {request.acting_as or 'general advisor'}

{self.EXPERTISE_AREAS}

{self.RESPONSE_STYLE}
"""
    
    def get_intent_prompt(self, intent: str, **kwargs) -> str:
        """Get intent-specific prompt"""
        base_prompt = self.get_base_prompt()
        intent_prompt = self.INTENT_PROMPTS.get(intent, self.INTENT_PROMPTS["explain_clause"])
        
        # Format the intent prompt with provided kwargs
        formatted_intent = intent_prompt.format(**kwargs)
        
        return f"{base_prompt}\n\n{formatted_intent}"
    
    def get_explain_clause_prompt(self, clause_key: str, transaction_context: str = "") -> str:
        """Get prompt for explaining clauses"""
        return self.get_intent_prompt(
            "explain_clause",
            clause_key=clause_key or "requested clause"
        )
    
    def get_revise_clause_prompt(self, clause_key: str, new_value: Dict[str, Any], user_message: str) -> str:
        """Get prompt for revising clauses"""
        return self.get_intent_prompt(
            "revise_clause",
            clause_key=clause_key or "clause",
            new_value=new_value,
            user_message=user_message
        )
    
    def get_simulate_trade_prompt(self, clause_key: str, user_message: str) -> str:
        """Get prompt for simulating trades"""
        return self.get_intent_prompt(
            "simulate_trade",
            clause_key=clause_key or "clause",
            user_message=user_message
        )
    
    def get_available_intents(self) -> List[str]:
        """Get list of available intents with descriptions"""
        return [
            {
                "intent": "explain_clause",
                "description": "Explain specific term sheet clauses and their implications",
                "llm_task": True,
                "batna_aware": True
            },
            {
                "intent": "revise_clause", 
                "description": "Review and suggest revisions to term sheet clauses",
                "llm_task": True,
                "batna_aware": True
            },
            {
                "intent": "simulate_trade",
                "description": "Simulate trade negotiations between different terms",
                "llm_task": True,
                "batna_aware": True
            },
            {
                "intent": "general_chat",
                "description": "General VC lawyer advice and consultation",
                "llm_task": True,
                "batna_aware": True
            }
        ]
    
    def get_ui_features(self) -> List[str]:
        """Get list of UI/UX features that shouldn't be LLM tasks"""
        return [
            {
                "feature": "update_persona",
                "description": "Persona creation and management",
                "implementation": "Form-based UI with real-time ZOPA computation",
                "llm_role": "Explain what persona attributes mean, not create them"
            },
            {
                "feature": "regenerate_document",
                "description": "Term sheet generation and regeneration", 
                "implementation": "NegotiationOrchestrator.run_round() + frontend redlining",
                "llm_role": "Explain generated terms, not generate them"
            }
        ]


# Global prompt service instance
prompt_service = PromptService()
