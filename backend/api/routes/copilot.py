"""Enhanced copilot routes with BATNA analysis capabilities."""
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.copilot_service import copilot_service


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    message: str


class ClauseAnalysisRequest(BaseModel):
    clause_key: str
    clause_title: str
    clause_text: str
    attributes: Dict[str, Any]
    leverage: Dict[str, float]


class ClauseAnalysisResponse(BaseModel):
    analysis: str


router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Generate a copilot response using OpenRouter."""
    try:
        history_payload: List[Dict[str, str]] = [msg.dict() for msg in request.history]
        reply = await copilot_service.handle_chat(request.message, history_payload)
        return ChatResponse(message=reply)
    except Exception as exc:  # pragma: no cover - simple error surfacing
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze-clause", response_model=ClauseAnalysisResponse)
async def analyze_clause(request: ClauseAnalysisRequest) -> ClauseAnalysisResponse:
    """Generate reasoned clause analysis using BATNA framework."""
    try:
        analysis = await copilot_service.analyze_clause(
            clause_key=request.clause_key,
            clause_title=request.clause_title,
            clause_text=request.clause_text,
            attributes=request.attributes,
            leverage=request.leverage
        )
        return ClauseAnalysisResponse(analysis=analysis)
    except Exception as exc:  # pragma: no cover - simple error surfacing
        raise HTTPException(status_code=500, detail=str(exc))
