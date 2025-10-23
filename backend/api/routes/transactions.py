from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from ..models.schemas import (
    TransactionCreateRequest, TransactionResponse,
    TransactionPersonaLinkRequest, TransactionPersonaResponse,
    ErrorResponse
)
from ..services.supabase import get_supabase_client

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    request: TransactionCreateRequest,
    supabase = Depends(get_supabase_client)
):
    """Create a new transaction"""
    try:
        # Create transaction
        transaction_data = {
            "owner_user": "00000000-0000-0000-0000-000000000000",  # Placeholder for now
            "name": request.name
        }
        
        result = supabase.table("transactions").insert(transaction_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create transaction")
        
        transaction = result.data[0]
        return TransactionResponse(
            id=transaction["id"],
            name=transaction["name"],
            created_at=transaction["created_at"],
            owner_user=transaction["owner_user"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    supabase = Depends(get_supabase_client)
):
    """List my transactions"""
    try:
        # For now, return all transactions (in production, filter by user)
        result = supabase.table("transactions").select("*").execute()
        
        transactions = []
        for tx in result.data:
            transactions.append(TransactionResponse(
                id=tx["id"],
                name=tx["name"],
                created_at=tx["created_at"],
                owner_user=tx["owner_user"]
            ))
        
        return transactions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{transaction_id}/personas", response_model=TransactionPersonaResponse)
async def link_persona_to_transaction(
    transaction_id: UUID,
    request: TransactionPersonaLinkRequest,
    supabase = Depends(get_supabase_client)
):
    """Link a persona to a transaction (create new or link existing)"""
    try:
        persona_id = None
        
        if request.persona_id:
            # Link existing persona
            persona_id = request.persona_id
        elif request.attrs:
            # Create new persona
            persona_data = {
                "owner_user": "00000000-0000-0000-0000-000000000000",
                "kind": "company" if request.kind == "company" else "investor",
                "attrs": request.attrs,
                "leverage_score": 0.5,
                "weights": {"exclusivity": 0.5, "vesting": 0.5},
                "batna": {}
            }
            
            result = supabase.table("personas").insert(persona_data).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create persona")
            persona_id = result.data[0]["id"]
        else:
            raise HTTPException(status_code=400, detail="Must provide either persona_id or attrs")
        
        # Link to transaction
        link_data = {
            "transaction_id": str(transaction_id),
            "kind": request.kind,
            "label": request.label,
            "persona_id": str(persona_id)
        }
        
        result = supabase.table("transaction_personas").insert(link_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to link persona to transaction")
        
        link = result.data[0]
        return TransactionPersonaResponse(
            id=link["id"],
            transaction_id=link["transaction_id"],
            kind=link["kind"],
            label=link["label"],
            persona_id=link["persona_id"],
            created_at=link["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transaction_id}/personas", response_model=List[TransactionPersonaResponse])
async def list_transaction_personas(
    transaction_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """List personas in a transaction"""
    try:
        result = supabase.table("transaction_personas").select("*").eq("transaction_id", str(transaction_id)).execute()
        
        personas = []
        for tp in result.data:
            personas.append(TransactionPersonaResponse(
                id=tp["id"],
                transaction_id=tp["transaction_id"],
                kind=tp["kind"],
                label=tp["label"],
                persona_id=tp["persona_id"],
                created_at=tp["created_at"]
            ))
        
        return personas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
