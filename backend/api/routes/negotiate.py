"""
Negotiation endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from uuid import UUID

from ..models.schemas import (
    NegotiationRoundRequest,
    NegotiationRoundResponse,
    NegotiationSessionCreate,
    NegotiationSessionResponse,
    SessionTermUpdate,
    SessionTermResponse,
    ErrorResponse
)
from ..engine.orchestrator import NegotiationOrchestrator
from ..services.supabase import get_supabase_client

router = APIRouter(prefix="/api/negotiate", tags=["negotiation"])


@router.post("/session", response_model=NegotiationSessionResponse)
async def create_session(
    request: NegotiationSessionCreate,
    supabase = Depends(get_supabase_client)
):
    """
    Create a new negotiation session
    
    Links a company and investor persona for negotiation
    """
    try:
        # TODO: Get user_id from auth
        user_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
        
        session_data = {
            "owner_user": user_id,
            "company_persona": str(request.company_persona),
            "investor_persona": str(request.investor_persona),
            "transaction_id": str(request.transaction_id),
            "regime": request.regime,
            "status": request.status
        }
        
        result = supabase.table("negotiation_sessions").insert(session_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return NegotiationSessionResponse(**result.data[0])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/round", response_model=NegotiationRoundResponse)
async def run_negotiation_round(
    request: NegotiationRoundRequest,
    supabase = Depends(get_supabase_client)
):
    """
    Execute a negotiation round
    
    Returns:
    - Final terms (mediator choice)
    - Per-clause traces with rationales
    - Citations (embedded snippets)
    - Utilities for both parties
    - Confidence/grounding scores
    """
    try:
        orchestrator = NegotiationOrchestrator(supabase)
        
        result = await orchestrator.run_round(
            session_id=request.session_id,
            round_no=request.round_no,
            user_overrides=request.user_overrides
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=NegotiationSessionResponse)
async def get_session(
    session_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """Get negotiation session by ID"""
    try:
        result = supabase.table("negotiation_sessions").select("*").eq(
            "id", str(session_id)
        ).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return NegotiationSessionResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/terms")
async def get_session_terms(
    session_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """Get all terms for a session"""
    try:
        result = supabase.table("session_terms").select("*").eq(
            "session_id", str(session_id)
        ).execute()
        
        terms = []
        if result.data:
            for row in result.data:
                terms.append(SessionTermResponse(**row))
        
        return terms
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/session/{session_id}/terms/{clause_key}", response_model=SessionTermResponse)
async def update_session_term(
    session_id: UUID,
    clause_key: str,
    request: SessionTermUpdate,
    supabase = Depends(get_supabase_client)
):
    """
    Update or pin a specific term in a session
    
    Can be used for manual overrides
    """
    try:
        term_data = {
            "session_id": str(session_id),
            "clause_key": clause_key,
            "value": request.value,
            "source": request.source,
            "confidence": request.confidence,
            "pinned_by": request.pinned_by
        }
        
        result = supabase.table("session_terms").upsert(term_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to update term")
        
        return SessionTermResponse(**result.data[0])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/rounds")
async def get_session_rounds(
    session_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """Get all negotiation rounds for a session"""
    try:
        result = supabase.table("negotiation_rounds").select("*").eq(
            "session_id", str(session_id)
        ).order("round_no").execute()
        
        return result.data or []
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

