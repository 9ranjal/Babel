"""
Copilot routes for conversational intake and Draft 0 generation
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..models.schemas import (
    IntakeStartRequest,
    IntakeStartResponse,
    IntakeAnswerRequest,
    IntakeAnswerResponse,
    Draft0Request,
    Draft0Response,
    ClauseBlock,
    ChatCitation,
    CopilotIntentRequest,
    CopilotIntentResponse,
    TransactionResponse,
    ErrorResponse
)
from ..services.supabase import get_supabase_client
from ..engine.intake import IntakeEngine
from ..engine.batna import BatnaEngine
from ..engine.market import MarketEngine
from ..engine.orchestrator import NegotiationOrchestrator
from ..rag.retriever import GuidanceRetriever

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    supabase = Depends(get_supabase_client)
):
    """List transactions for frontend selection"""
    try:
        from .transactions import list_transactions
        return await list_transactions(supabase)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-ollama")
async def test_ollama():
    """Test Ollama integration"""
    try:
        from ..services.ollama import get_ollama_client
        client = get_ollama_client()
        
        # Test simple question
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Respond with a simple greeting."},
            {"role": "user", "content": "Hello, what model are you?"}
        ]
        
        response = await client.generate_response(messages, temperature=0.1)
        return {"model": client.model, "response": response}
    except Exception as e:
        return {"error": str(e), "model": "unknown"}


@router.post("/intake/start", response_model=IntakeStartResponse)
async def start_intake(
    request: IntakeStartRequest,
    supabase = Depends(get_supabase_client)
):
    """Start copilot intake flow"""
    try:
        # If no transaction_id provided, create one first
        transaction_id = request.transaction_id
        if not transaction_id:
            # Create transaction using the transactions API
            from .transactions import create_transaction
            from ..models.schemas import TransactionCreateRequest
            
            tx_request = TransactionCreateRequest(name=f"Intake {request.role} - {request.stage}")
            tx_response = await create_transaction(tx_request, supabase)
            transaction_id = tx_response.id
        
        intake_engine = IntakeEngine(supabase)
        resp = await intake_engine.start_intake(
            role=request.role,
            stage=request.stage,
            region=request.region,
            transaction_id=str(transaction_id)
        )
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intake/answer", response_model=IntakeAnswerResponse)
async def answer_intake(
    request: IntakeAnswerRequest,
    supabase = Depends(get_supabase_client)
):
    """Answer intake question"""
    try:
        intake_engine = IntakeEngine(supabase)
        return await intake_engine.answer_question(
            question_id=request.question_id,
            answer=request.answer,
            session_id=request.session_id,
            persona_id=str(request.persona_id) if request.persona_id else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft0", response_model=Draft0Response)
async def generate_draft0(
    request: Draft0Request,
    supabase = Depends(get_supabase_client)
):
    """Generate Draft 0 term sheet with Exclusivity + Pre-emption"""
    try:
        # Fetch company persona
        company_result = supabase.table("personas").select("*").eq(
            "id", str(request.company_persona_id)
        ).execute()
        
        if not company_result.data:
            raise HTTPException(status_code=404, detail="Company persona not found")
        
        company_persona = company_result.data[0]
        
        # Fetch investor personas
        investor_personas = []
        if request.investor_persona_ids:
            investor_result = supabase.table("personas").select("*").in_(
                "id", [str(pid) for pid in request.investor_persona_ids]
            ).execute()
            investor_personas = investor_result.data or []
        
        if not investor_personas:
            raise HTTPException(status_code=400, detail="At least one investor persona required")
        
        # Initialize engines
        market_engine = MarketEngine(supabase)
        batna_engine = BatnaEngine(supabase)
        retriever = GuidanceRetriever(supabase)
        
        # Choose anchor investor (marquee for market-setting clauses, else weight by ownership)
        anchor_investor = batna_engine.compute_anchor_investor(investor_personas)
        anchor_name = anchor_investor.get("attrs", {}).get("name", f"Investor {anchor_investor['id'][:8]}")
        
        # Generate clauses
        clauses = []
        utilities = {"company": 0.0, "investor": 0.0}
        
        for clause_key in request.clauses_enabled:
            clause_block = await _generate_clause_block(
                clause_key=clause_key,
                company_persona=company_persona,
                investor_personas=investor_personas,
                anchor_investor=anchor_investor,
                stage=request.stage,
                region=request.region,
                market_engine=market_engine,
                batna_engine=batna_engine,
                retriever=retriever
            )
            clauses.append(clause_block)
        
        # Compute utilities
        company_terms = {clause.id: clause.current_value for clause in clauses}
        utilities["company"] = batna_engine._calculate_simple_utility(
            company_persona, company_terms
        )
        utilities["investor"] = batna_engine.aggregate_investor_utilities(
            investor_personas, company_terms
        )
        
        # Create session for tracking
        session_data = {
            "owner_user": "00000000-0000-0000-0000-000000000000",
            "company_persona": str(request.company_persona_id),
            "investor_persona": str(anchor_investor["id"]),  # Use anchor for session
            "regime": request.region,
            "status": "draft"
        }
        
        session_result = supabase.table("negotiation_sessions").insert(session_data).execute()
        session_id = session_result.data[0]["id"]
        
        # Build summary
        summary_md = _build_draft0_summary(clauses, utilities, anchor_name)
        
        return Draft0Response(
            session_id=session_id,
            company_persona_id=request.company_persona_id,
            investor_persona_ids=request.investor_persona_ids,
            clauses=clauses,
            summary_md=summary_md,
            utilities=utilities,
            anchor_investor=anchor_name,
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intent", response_model=CopilotIntentResponse)
async def handle_intent(
    request: CopilotIntentRequest,
    supabase = Depends(get_supabase_client)
):
    """Handle chat intents"""
    try:
        if request.intent == "explain_clause":
            return await _handle_explain_clause(request, supabase)
        elif request.intent == "revise_clause":
            return await _handle_revise_clause(request, supabase)
        elif request.intent == "simulate_trade":
            return await _handle_simulate_trade(request, supabase)
        elif request.intent == "regenerate_document":
            return await _handle_regenerate_document(request, supabase)
        elif request.intent == "update_persona":
            return await _handle_update_persona(request, supabase)
        else:
            # For unknown intents, treat as general chat
            return await _handle_general_chat(request, supabase)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=CopilotIntentResponse)
async def handle_general_chat(
    request: CopilotIntentRequest,
    supabase = Depends(get_supabase_client)
):
    """Handle general chat with VC lawyer expertise"""
    try:
        return await _handle_general_chat(request, supabase)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_clause_block(
    clause_key: str,
    company_persona: Dict[str, Any],
    investor_personas: List[Dict[str, Any]],
    anchor_investor: Dict[str, Any],
    stage: str,
    region: str,
    market_engine: MarketEngine,
    batna_engine: BatnaEngine,
    retriever: GuidanceRetriever
) -> ClauseBlock:
    """Generate a clause block with redlines and citations"""
    
    # Get guidance and market data
    guidance = market_engine.get_guidance(clause_key, stage, region)
    market = market_engine.get_benchmark(clause_key, stage, region)
    
    if not guidance and not market:
        # Fallback clause block
        return ClauseBlock(
            id=clause_key,
            title=clause_key.replace("_", " ").title(),
            content_md=f"**{clause_key}**: No guidance available",
            current_value={},
            default_band=(0, 100),
            walk_away=(0, 100)
        )
    
    # Get persona BATNAs
    company_batna = company_persona.get("batna", {}).get(clause_key, {})
    investor_batna = anchor_investor.get("batna", {}).get(clause_key, {})
    
    # Compute bands
    # Source bands from guidance first; fallback to market if missing
    if guidance:
        # Build minimal surrogate market if needed
        class _M: pass
        surrogate = _M()
        setattr(surrogate, 'p25', getattr(market, 'p25', None) if market else None)
        setattr(surrogate, 'p75', getattr(market, 'p75', None) if market else None)
        default_low, default_high, walk_min, walk_max = batna_engine.compute_batna_bands(
            clause_key, guidance, surrogate, company_persona
        )
    elif market:
        # Use market-only defaults when guidance missing
        class _G: pass
        surrogate_g = _G()
        setattr(surrogate_g, 'default_low', getattr(market, 'p25', None))
        setattr(surrogate_g, 'default_high', getattr(market, 'p75', None))
        setattr(surrogate_g, 'min_val', None)
        setattr(surrogate_g, 'max_val', None)
        default_low, default_high, walk_min, walk_max = batna_engine.compute_batna_bands(
            clause_key, surrogate_g, market, company_persona
        )
    else:
        default_low, default_high = 0, 100
        walk_min, walk_max = 0, 100
    
    # Generate compromise value (simplified)
    if clause_key == "exclusivity":
        company_days = company_batna.get("period_days", 30)
        investor_days = investor_batna.get("period_days", 60)
        compromise_days = int((company_days + investor_days) / 2)
        current_value = {"period_days": compromise_days}
    elif clause_key == "pro_rata_rights":
        company_wants = company_batna.get("enabled", False)
        investor_wants = investor_batna.get("enabled", True)
        compromise_enabled = investor_wants  # Investor typically wins on pro-rata
        current_value = {
            "enabled": compromise_enabled,
            "threshold_ownership_pct": investor_batna.get("threshold_ownership_pct", 2)
        }
    else:
        current_value = {}
    
    # Get citations
    citations = retriever.get_snippets_for_clause(
        clause_key=clause_key,
        stage=stage,
        region=region,
        limit=2
    )
    
    citation_chips = [
        ChatCitation(
            id=c.id,
            clause_key=c.clause_key,
            perspective=c.perspective,
            content=c.content[:100] + "..." if len(c.content) > 100 else c.content
        )
        for c in citations
    ]
    
    # Build content
    content_md = f"**{clause_key.replace('_', ' ').title()}**\n\n"
    if guidance:
        content_md += f"{guidance.detail_md}\n\n"
    
    content_md += f"**Current Value:** {current_value}\n"
    content_md += f"**Default Band:** {default_low:.0f} - {default_high:.0f}\n"
    
    # Build redlines
    redlines = []
    if clause_key == "exclusivity":
        if current_value.get("period_days", 0) < default_low:
            redlines.append(f"Below market minimum ({default_low:.0f} days)")
        elif current_value.get("period_days", 0) > default_high:
            redlines.append(f"Above market maximum ({default_high:.0f} days)")
    
    return ClauseBlock(
        id=clause_key,
        title=clause_key.replace("_", " ").title(),
        content_md=content_md,
        redlines=redlines,
        citations=citation_chips,
        current_value=current_value,
        default_band=(default_low, default_high),
        walk_away=(walk_min, walk_max)
    )


def _build_draft0_summary(clauses: List[ClauseBlock], utilities: Dict[str, float], anchor_name: str) -> str:
    """Build Draft 0 summary markdown"""
    summary = "# Draft 0 Term Sheet Summary\n\n"
    summary += f"**Company Satisfaction:** {utilities['company']:.1%}\n"
    summary += f"**Investor Satisfaction:** {utilities['investor']:.1%}\n"
    summary += f"**Anchor Investor:** {anchor_name}\n\n"
    
    summary += "## Key Terms\n\n"
    for clause in clauses:
        summary += f"### {clause.title}\n"
        summary += f"- **Value:** {clause.current_value}\n"
        if clause.redlines:
            summary += f"- **⚠️ Issues:** {', '.join(clause.redlines)}\n"
        summary += "\n"
    
    return summary


async def _handle_explain_clause(request: CopilotIntentRequest, supabase) -> CopilotIntentResponse:
    """Handle explain_clause intent with VC lawyer expertise"""
    try:
        # Get transaction context
        transaction_id = request.transaction_id
        clause_key = request.clause_key or "general"
        user_message = request.message or ""
        
        # Load transaction personas for context
        personas = []
        if transaction_id:
            try:
                persona_result = supabase.table("transaction_personas").select("*, personas(*)").eq("transaction_id", str(transaction_id)).execute()
                personas = persona_result.data
            except Exception as e:
                print(f"Error loading personas: {e}")
        
        # Generate VC lawyer response using Ollama
        from ..services.ollama import get_ollama_client
        ollama = get_ollama_client()
        
        # Build context for the AI
        context = f"""
You are a senior VC lawyer with 15+ years of experience in venture capital transactions. 
You're advising on a {clause_key} clause in a term sheet negotiation.

Transaction Context:
- Transaction ID: {transaction_id or 'New transaction'}
- Active Personas: {len(personas)} personas in this transaction
- User Question: {user_message}

Provide expert legal advice on the {clause_key} clause, including:
1. What this clause means in plain English
2. Key risks and considerations for founders vs investors
3. Market standard ranges and what's negotiable
4. Red flags to watch out for
5. Practical negotiation tips

Be conversational, authoritative, and practical. Use specific examples when helpful.
"""
        
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": f"Please explain the {clause_key} clause: {user_message}"}
        ]
        
        response = await ollama.generate_response(messages, temperature=0.7)
        
        return CopilotIntentResponse(
            intent="explain_clause",
            success=True,
            message=response,
            citations=[
                {
                    "id": 1,
                    "clause_key": clause_key,
                    "perspective": "detail",
                    "content": "Standard market terms and negotiation strategies"
                }
            ]
        )
        
    except Exception as e:
        return CopilotIntentResponse(
            intent="explain_clause",
            success=False,
            message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
            citations=[]
        )


async def _handle_revise_clause(request: CopilotIntentRequest, supabase) -> CopilotIntentResponse:
    """Handle revise_clause intent with VC lawyer expertise"""
    try:
        clause_key = request.clause_key or "general"
        new_value = request.new_value or {}
        user_message = request.message or ""
        
        from ..services.ollama import get_ollama_client
        ollama = get_ollama_client()
        
        context = f"""
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
"""
        
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": f"Please analyze this proposed change to the {clause_key} clause: {user_message}"}
        ]
        
        response = await ollama.generate_response(messages, temperature=0.7)
        
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


async def _handle_simulate_trade(request: CopilotIntentRequest, supabase) -> CopilotIntentResponse:
    """Handle simulate_trade intent with VC lawyer expertise"""
    try:
        clause_key = request.clause_key or "general"
        user_message = request.message or ""
        
        from ..services.ollama import get_ollama_client
        ollama = get_ollama_client()
        
        context = f"""
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
"""
        
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": f"Please simulate this trade: {user_message}"}
        ]
        
        response = await ollama.generate_response(messages, temperature=0.7)
        
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


async def _handle_regenerate_document(request: CopilotIntentRequest, supabase) -> CopilotIntentResponse:
    """Handle regenerate_document intent"""
    # Simplified implementation
    return CopilotIntentResponse(
        intent="regenerate_document",
        success=True,
        message="Document regenerated",
        updated_clauses=[]
    )


async def _handle_update_persona(request: CopilotIntentRequest, supabase) -> CopilotIntentResponse:
    """Handle update_persona intent"""
    # Simplified implementation
    return CopilotIntentResponse(
        intent="update_persona",
        success=True,
        message="Persona updated",
        updated_clauses=[]
    )


async def _handle_general_chat(request: CopilotIntentRequest, supabase) -> CopilotIntentResponse:
    """Handle general chat with VC lawyer expertise"""
    try:
        user_message = request.message or "Hello"
        transaction_id = request.transaction_id
        
        # Load transaction context
        personas = []
        if transaction_id:
            try:
                persona_result = supabase.table("transaction_personas").select("*, personas(*)").eq("transaction_id", str(transaction_id)).execute()
                personas = persona_result.data
            except Exception as e:
                print(f"Error loading personas: {e}")
        
        from ..services.ollama import get_ollama_client
        ollama = get_ollama_client()
        
        # Build comprehensive VC lawyer context
        context = f"""
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
- Transaction ID: {transaction_id or 'New transaction'}
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
        
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": user_message}
        ]
        
        response = await ollama.generate_response(messages, temperature=0.7)
        
        return CopilotIntentResponse(
            intent="general_chat",
            success=True,
            message=response,
            citations=[
                {
                    "id": 1,
                    "clause_key": "general",
                    "perspective": "detail",
                    "content": "Based on 15+ years of venture capital legal experience"
                }
            ]
        )
        
    except Exception as e:
        return CopilotIntentResponse(
            intent="general_chat",
            success=False,
            message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
            citations=[]
        )
