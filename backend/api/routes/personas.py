"""
Persona management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from ..models.schemas import (
    PersonaCreate,
    PersonaResponse,
    ErrorResponse
)
from ..services.supabase import get_supabase_client

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.post("/", response_model=PersonaResponse)
async def create_persona(
    request: PersonaCreate,
    supabase = Depends(get_supabase_client)
):
    """
    Create a new persona (company or investor profile)
    
    This builds the negotiation profile with:
    - Basic attributes (stage, sector, fund size, etc.)
    - Leverage score (how strong is their position?)
    - Weights (which clauses matter most?)
    - BATNA (ideal values for each clause)
    """
    try:
        # TODO: Get user_id from auth
        user_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
        
        persona_data = {
            "owner_user": user_id,
            "kind": request.kind,
            "attrs": request.attrs,
            "leverage_score": request.leverage_score,
            "weights": request.weights,
            "batna": request.batna
        }
        
        result = supabase.table("personas").insert(persona_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create persona")
        
        return PersonaResponse(**result.data[0])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[PersonaResponse])
async def list_personas(
    kind: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    List all personas for the current user
    
    Optional filter by kind: 'company' or 'investor'
    """
    try:
        # TODO: Get user_id from auth
        user_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
        
        query = supabase.table("personas").select("*").eq("owner_user", user_id)
        
        if kind:
            query = query.eq("kind", kind)
        
        result = query.order("created_at", desc=True).execute()
        
        personas = []
        if result.data:
            for row in result.data:
                personas.append(PersonaResponse(**row))
        
        return personas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """Get a specific persona by ID"""
    try:
        result = supabase.table("personas").select("*").eq(
            "id", str(persona_id)
        ).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        return PersonaResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: UUID,
    request: PersonaCreate,
    supabase = Depends(get_supabase_client)
):
    """
    Update an existing persona
    
    Allows you to refine:
    - Attributes (company/investor details)
    - Leverage score
    - Clause weights (priorities)
    - BATNA (ideal outcomes)
    """
    try:
        persona_data = {
            "kind": request.kind,
            "attrs": request.attrs,
            "leverage_score": request.leverage_score,
            "weights": request.weights,
            "batna": request.batna
        }
        
        result = supabase.table("personas").update(persona_data).eq(
            "id", str(persona_id)
        ).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        return PersonaResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """Delete a persona"""
    try:
        result = supabase.table("personas").delete().eq(
            "id", str(persona_id)
        ).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        return {"ok": True, "message": "Persona deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-leverage")
async def calculate_leverage(
    persona_data: dict,
    supabase = Depends(get_supabase_client)
):
    """
    Calculate leverage score for a persona based on attributes
    
    This is a helper endpoint that applies heuristics to estimate
    negotiation strength from company/investor attributes.
    
    For companies:
    - Higher revenue → higher leverage
    - More traction → higher leverage
    - Multiple term sheets → higher leverage
    
    For investors:
    - Bigger fund → higher leverage
    - Better brand → higher leverage
    - Competitive market → lower leverage
    """
    try:
        kind = persona_data.get("kind")
        attrs = persona_data.get("attrs", {})
        
        if kind == "company":
            leverage = _calculate_company_leverage(attrs)
        elif kind == "investor":
            leverage = _calculate_investor_leverage(attrs)
        else:
            raise HTTPException(status_code=400, detail="Invalid persona kind")
        
        return {
            "leverage_score": leverage,
            "explanation": _get_leverage_explanation(kind, leverage, attrs)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_company_leverage(attrs: dict) -> float:
    """
    Calculate company leverage score (0.0 - 1.0)
    
    Factors:
    - Revenue/traction
    - Team quality
    - Multiple offers
    - Market conditions
    """
    leverage = 0.5  # Baseline
    
    # Revenue factor
    revenue = attrs.get("revenue_run_rate", 0)
    if revenue > 5000000:
        leverage += 0.2
    elif revenue > 1000000:
        leverage += 0.15
    elif revenue > 100000:
        leverage += 0.1
    
    # Multiple term sheets
    if attrs.get("competing_offers", 0) > 0:
        leverage += 0.1
    
    # Strong team
    if attrs.get("team_size", 0) > 10:
        leverage += 0.05
    
    # Cap at 1.0
    return min(1.0, leverage)


def _calculate_investor_leverage(attrs: dict) -> float:
    """
    Calculate investor leverage score (0.0 - 1.0)
    
    Factors:
    - Fund size
    - Brand/reputation
    - Market competitiveness
    """
    leverage = 0.5  # Baseline
    
    # Fund size factor
    fund_size = attrs.get("fund_size", 0)
    if fund_size > 500000000:
        leverage += 0.15
    elif fund_size > 100000000:
        leverage += 0.1
    
    # Brand/tier
    tier = attrs.get("tier", "").lower()
    if tier == "tier-1":
        leverage += 0.1
    elif tier == "tier-2":
        leverage += 0.05
    
    # Market conditions (hot market = lower investor leverage)
    if attrs.get("market_competitive", False):
        leverage -= 0.15
    
    # Cap between 0.0 and 1.0
    return max(0.0, min(1.0, leverage))


def _get_leverage_explanation(kind: str, leverage: float, attrs: dict) -> str:
    """Generate human-readable explanation of leverage score"""
    if leverage > 0.7:
        strength = "Strong"
    elif leverage > 0.5:
        strength = "Moderate"
    else:
        strength = "Weak"
    
    if kind == "company":
        factors = []
        if attrs.get("revenue_run_rate", 0) > 1000000:
            factors.append("strong revenue traction")
        if attrs.get("competing_offers", 0) > 0:
            factors.append(f"{attrs['competing_offers']} competing offers")
        
        if factors:
            return f"{strength} position due to: {', '.join(factors)}"
        else:
            return f"{strength} position (early stage)"
    else:
        factors = []
        if attrs.get("fund_size", 0) > 100000000:
            factors.append("large fund size")
        if attrs.get("tier") == "tier-1":
            factors.append("tier-1 brand")
        
        if factors:
            return f"{strength} position due to: {', '.join(factors)}"
        else:
            return f"{strength} position"

