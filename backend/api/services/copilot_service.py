"""
Copilot Service Layer
Handles all copilot business logic with proper separation of concerns
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from ..models.schemas import CopilotIntentRequest, CopilotIntentResponse
from ..services.ollama import get_ollama_client
from ..services.openrouter import get_openrouter_client
from ..services.supabase import get_supabase_client
from ..core.settings import settings
from .prompt_service import prompt_service
from .batna_aware_prompt_service import get_batna_aware_prompt_service


class CopilotService:
    """Main copilot service handling all AI interactions"""
    
    def __init__(self):
        self.ollama = get_ollama_client()
        self.openrouter = get_openrouter_client()
        self.batna_prompt_service = None  # Will be initialized with supabase client
    
    async def handle_general_chat(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        """Handle general VC lawyer conversations"""
        try:
            # Load transaction context
            personas = await self._load_transaction_context(request.transaction_id)
            
            # Build VC lawyer context using centralized prompt service
            context = prompt_service.get_general_chat_prompt(request, personas)
            
            # Generate AI response
            response = await self._generate_ai_response(context, request.message)
            
            return CopilotIntentResponse(
                intent="general_chat",
                success=True,
                message=response,
                citations=[{
                    "id": 1,
                    "clause_key": "general",
                    "perspective": "detail",
                    "content": "Based on 15+ years of venture capital legal experience"
                }]
            )
            
        except Exception as e:
            return CopilotIntentResponse(
                intent="general_chat",
                success=False,
                message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                citations=[]
            )
    
    async def handle_explain_clause(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        """Handle clause explanation requests with BATNA awareness"""
        try:
            personas = await self._load_transaction_context(request.transaction_id)
            
            # Initialize BATNA-aware prompt service if needed
            if not self.batna_prompt_service:
                supabase = get_supabase_client()
                self.batna_prompt_service = get_batna_aware_prompt_service(supabase)
            
            # Use BATNA-aware prompt for more intelligent responses
            if request.transaction_id and personas:
                context = self.batna_prompt_service.get_batna_enhanced_prompt(
                    "explain_clause",
                    request.clause_key or "general",
                    request.transaction_id,
                    personas,
                    clause_key=request.clause_key or "requested clause"
                )
            else:
                # Fallback to basic prompt
                context = prompt_service.get_explain_clause_prompt(
                    request.clause_key,
                    f"Transaction ID: {request.transaction_id or 'New transaction'}\nActive Personas: {len(personas)} personas\nActing as: {request.acting_as or 'general advisor'}"
                )
            
            response = await self._generate_ai_response(context, request.message)
            
            return CopilotIntentResponse(
                intent="explain_clause",
                success=True,
                message=response,
                citations=[{
                    "id": 1,
                    "clause_key": request.clause_key or "general",
                    "perspective": "detail",
                    "content": "BATNA-aware analysis based on actual persona leverage and preferences"
                }]
            )
            
        except Exception as e:
            return CopilotIntentResponse(
                intent="explain_clause",
                success=False,
                message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                citations=[]
            )
    
    async def handle_revise_clause(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        """Handle clause revision requests"""
        try:
            personas = await self._load_transaction_context(request.transaction_id)
            
            context = f"""
You are a senior VC lawyer reviewing a proposed change to a {request.clause_key or 'clause'}.

Proposed Change: {request.new_value or {}}
User Request: {request.message or ''}

Provide expert analysis including:
1. Whether this change is reasonable and market-standard
2. Potential risks or red flags
3. Alternative approaches or compromises
4. Negotiation strategy recommendations
5. What to ask for in return

Be practical and specific about negotiation tactics.
"""
            
            response = await self._generate_ai_response(context, request.message)
            
            return CopilotIntentResponse(
                intent="revise_clause",
                success=True,
                message=response,
                updated_clauses=[],
                suggested_trades=[]
            )
            
        except Exception as e:
            return CopilotIntentResponse(
                intent="revise_clause",
                success=False,
                message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                updated_clauses=[]
            )
    
    async def handle_simulate_trade(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        """Handle trade simulation requests"""
        try:
            personas = await self._load_transaction_context(request.transaction_id)
            
            context = f"""
You are a senior VC lawyer helping simulate a trade negotiation for a {request.clause_key or 'clause'}.

User Request: {request.message or ''}

Provide a detailed trade simulation including:
1. What you're giving up vs what you're getting
2. Market precedent for this type of trade
3. Risk assessment of the trade
4. Alternative trade structures
5. Negotiation tactics and timing
6. Potential counter-offers to expect

Be specific about the trade mechanics and negotiation strategy.
"""
            
            response = await self._generate_ai_response(context, request.message)
            
            return CopilotIntentResponse(
                intent="simulate_trade",
                success=True,
                message=response,
                suggested_trades=[]
            )
            
        except Exception as e:
            return CopilotIntentResponse(
                intent="simulate_trade",
                success=False,
                message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                suggested_trades=[]
            )
    
    async def _load_transaction_context(self, transaction_id: Optional[UUID]) -> List[Dict[str, Any]]:
        """Load transaction personas for context"""
        if not transaction_id:
            return []
        
        try:
            supabase = get_supabase_client()
            result = supabase.table("transaction_personas").select("*, personas(*)").eq("transaction_id", str(transaction_id)).execute()
            return result.data
        except Exception as e:
            print(f"Error loading personas: {e}")
            return []
    
    def _build_vc_lawyer_context(self, request: CopilotIntentRequest, personas: List[Dict[str, Any]]) -> str:
        """Build comprehensive VC lawyer context"""
        return f"""
You are a senior VC lawyer with 15+ years of experience in venture capital transactions, specializing in:
- Series A, B, C, and growth stage financings
- Founder-friendly term sheet negotiations
- Investor protection mechanisms
- Exit strategy planning and execution
- Corporate governance and board dynamics
- Employment and equity compensation structures
- IP protection and assignment agreements
- Regulatory compliance for startups and VCs

TRANSACTION CONTEXT:
- Transaction ID: {request.transaction_id or 'New transaction'}
- Active Personas: {len(personas)} personas in this transaction
- Acting as: {request.acting_as or 'general advisor'}

EXPERTISE AREAS:
1. **Term Sheet Negotiation**: Liquidation preferences, anti-dilution, board composition, voting rights, drag-along rights, tag-along rights, preemptive rights, information rights, registration rights, redemption rights, conversion rights, dividend rights, protective provisions, and more.

2. **Market Standards**: Current market terms for different stages (seed, Series A, B, C), industry-specific variations, geographic differences (US vs EU vs Asia), and how market conditions affect term sheet structures.

3. **Risk Assessment**: Red flags in term sheets, founder protection mechanisms, investor control provisions, exit scenarios, and how to structure deals to minimize future conflicts.

4. **Negotiation Strategy**: Tactical advice on which terms to prioritize, how to structure trades, when to push back, and how to maintain good investor relationships while protecting founder interests.

5. **Legal Framework**: Securities law compliance, corporate law requirements, tax implications, regulatory considerations, and cross-border transaction complexities.

6. **Exit Planning**: IPO preparation, M&A considerations, liquidation scenarios, and how term sheet provisions affect exit outcomes.

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
    
    async def _generate_ai_response(self, context: str, user_message: str) -> str:
        """Generate AI response with configurable primary service and fallback"""
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": user_message}
        ]
        
        # Determine primary and fallback services based on configuration
        if settings.PRIMARY_AI_SERVICE.lower() == "openrouter":
            primary_service = self.openrouter
            fallback_service = self.ollama
            primary_name = "OpenRouter"
            fallback_name = "Ollama"
        else:
            primary_service = self.ollama
            fallback_service = self.openrouter
            primary_name = "Ollama"
            fallback_name = "OpenRouter"
        
        # Try primary service first
        try:
            return await primary_service.generate_response(messages, temperature=0.7)
        except Exception as primary_error:
            print(f"{primary_name} failed: {primary_error}, falling back to {fallback_name}...")
            
            # Fallback to secondary service
            try:
                return await fallback_service.generate_response(messages, temperature=0.7)
            except Exception as fallback_error:
                print(f"{fallback_name} also failed: {fallback_error}")
                # Final fallback - return a helpful error message
                return f"I apologize, but I'm having trouble connecting to my AI services right now. Please try again in a moment. ({primary_name}: {str(primary_error)[:100]}, {fallback_name}: {str(fallback_error)[:100]})"


# Service instance
copilot_service = CopilotService()
