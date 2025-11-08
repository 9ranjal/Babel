"""Minimal copilot chat routes."""
from typing import List, Dict

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
