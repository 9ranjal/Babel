"""Enhanced copilot routes with ZOPA analysis capabilities."""
from typing import List, Dict, Any, Optional

import httpx
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


def _chat_error_detail(exc: Exception) -> str:
    """Return a safe, user-facing message for chat failures."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 401:
            return "OpenRouter API key is invalid or missing. Set OPENROUTER_API_KEY in backend/.env"
        if status == 429:
            return "OpenRouter rate limit reached. Please try again in a moment."
        if status >= 500:
            return "OpenRouter is temporarily unavailable. Please try again later."
        try:
            body = exc.response.text
            if len(body) > 200:
                body = body[:200] + "..."
            return f"OpenRouter error ({status}): {body}"
        except Exception:
            return f"OpenRouter error: HTTP {status}"
    if isinstance(exc, (KeyError, IndexError)):
        return "Unexpected response from OpenRouter. Please try again."
    return str(exc) or "Chat request failed. Please try again."


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Generate a copilot response using OpenRouter."""
    try:
        history_payload: List[Dict[str, str]] = [
            msg.model_dump() for msg in request.history
        ]
        reply = await copilot_service.handle_chat(request.message, history_payload)
        return ChatResponse(message=reply)
    except httpx.HTTPStatusError as exc:
        detail = _chat_error_detail(exc)
        raise HTTPException(status_code=502, detail=detail)
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail=_chat_error_detail(exc),
        )
    except Exception as exc:  # pragma: no cover - simple error surfacing
        raise HTTPException(status_code=500, detail=_chat_error_detail(exc))


@router.post("/analyze-clause", response_model=ClauseAnalysisResponse)
async def analyze_clause(request: ClauseAnalysisRequest) -> ClauseAnalysisResponse:
    """Generate reasoned clause analysis using ZOPA framework."""
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
