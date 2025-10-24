"""
Copilot Routes V2 - Modular Architecture
Clean separation of concerns with service layer
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID

from ..models.schemas import (
    CopilotIntentRequest,
    CopilotIntentResponse,
    TransactionResponse
)
from ..services.supabase import get_supabase_client
from ..services.copilot_service import copilot_service
from ..services.intent_handlers import IntentHandlerFactory
from ..services.context_service import context_service
from ..services.prompt_service import prompt_service
from ..services.term_sheet_service import term_sheet_service

router = APIRouter(prefix="/api/copilot", tags=["copilot-v2"])


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


@router.post("/chat", response_model=CopilotIntentResponse)
async def handle_general_chat(
    request: CopilotIntentRequest,
    supabase = Depends(get_supabase_client)
):
    """Handle general chat with VC lawyer expertise"""
    try:
        return await copilot_service.handle_general_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intent", response_model=CopilotIntentResponse)
async def handle_intent(
    request: CopilotIntentRequest,
    supabase = Depends(get_supabase_client)
):
    """Handle specific copilot intents with modular handlers"""
    try:
        # Get appropriate handler for the intent
        handler = IntentHandlerFactory.get_handler(request.intent)
        
        # Handle the request
        return await handler.handle(request)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents")
async def list_available_intents():
    """List all available copilot intents"""
    return {
        "intents": IntentHandlerFactory.get_available_intents(),
        "description": "Available copilot intents for specialized responses"
    }


@router.get("/context/{transaction_id}")
async def get_transaction_context(
    transaction_id: UUID,
    supabase = Depends(get_supabase_client)
):
    """Get comprehensive transaction context for copilot"""
    try:
        context = await context_service.get_transaction_context(transaction_id)
        summary = context_service.build_context_summary(context)
        
        return {
            "transaction_id": str(transaction_id),
            "context": context,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def get_prompts():
    """Get all available prompts and their descriptions"""
    try:
        return {
            "base_prompt": prompt_service.get_base_prompt(),
            "available_intents": prompt_service.get_available_intents(),
            "ui_features": prompt_service.get_ui_features(),
            "intent_prompts": {
                intent: prompt_service.INTENT_PROMPTS[intent] 
                for intent in prompt_service.INTENT_PROMPTS.keys()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{intent}")
async def get_intent_prompt(intent: str):
    """Get specific intent prompt"""
    try:
        if intent not in prompt_service.INTENT_PROMPTS:
            raise HTTPException(status_code=404, detail=f"Intent '{intent}' not found")
        
        return {
            "intent": intent,
            "prompt": prompt_service.INTENT_PROMPTS[intent],
            "base_prompt": prompt_service.get_base_prompt()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-batna/{transaction_id}")
async def test_batna_aware_prompts(
    transaction_id: UUID,
    clause_key: str = "exclusivity",
    supabase = Depends(get_supabase_client)
):
    """Test BATNA-aware prompt generation"""
    try:
        from ..services.batna_aware_prompt_service import get_batna_aware_prompt_service
        
        # Get BATNA-aware prompt service
        batna_service = get_batna_aware_prompt_service(supabase)
        
        # Load transaction personas
        persona_result = supabase.table("transaction_personas").select("*, personas(*)").eq("transaction_id", str(transaction_id)).execute()
        personas = persona_result.data
        
        # Generate BATNA-aware prompt
        batna_prompt = batna_service.get_batna_enhanced_prompt(
            "explain_clause",
            clause_key,
            transaction_id,
            personas,
            user_message="Explain this clause with BATNA awareness"
        )
        
        # Generate negotiation strategy prompt
        strategy_prompt = batna_service.get_negotiation_strategy_prompt(
            clause_key,
            transaction_id,
            personas
        )
        
        return {
            "status": "success",
            "transaction_id": str(transaction_id),
            "clause_key": clause_key,
            "personas_count": len(personas),
            "batna_enhanced_prompt": batna_prompt,
            "strategy_prompt": strategy_prompt,
            "message": "BATNA-aware prompts generated successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"BATNA-aware prompt generation failed: {str(e)}"
        }


@router.get("/test-ollama")
async def test_ollama():
    """Test Ollama integration"""
    try:
        from ..services.ollama import get_ollama_client
        client = get_ollama_client()

        # Test basic connection
        response = await client.generate_response([
            {"role": "user", "content": "Hello, are you working?"}
        ], temperature=0.1)

        return {
            "status": "success",
            "response": response,
            "message": "Ollama integration is working"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Ollama integration failed: {str(e)}"
        }


@router.post("/generate-term-sheet")
async def generate_term_sheet(data: dict):
    """Generate term sheet from collected information"""
    try:
        # Validate and clean the data
        validated_data = term_sheet_service.validate_data(data)
        
        # Generate the term sheet
        term_sheet_content = term_sheet_service.generate_term_sheet(validated_data)
        
        return {
            "status": "success",
            "term_sheet": term_sheet_content,
            "data": validated_data,
            "message": "Term sheet generated successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Term sheet generation failed: {str(e)}"
        }
