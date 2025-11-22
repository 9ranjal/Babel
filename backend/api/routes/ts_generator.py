"""Term sheet generator API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.ts_generator import generate_term_sheet


class GenerateTSRequest(BaseModel):
    """Request model for term sheet generation."""
    nl_input: str


class GenerateTSResponse(BaseModel):
    """Response model for term sheet generation."""
    term_sheet: str
    deal_config: dict[str, Any]
    validation_errors: list[str]
    clarification_questions: list[str] | None


router = APIRouter(prefix="/ts-generator", tags=["ts-generator"])


@router.post("/generate", response_model=GenerateTSResponse)
async def generate(request: GenerateTSRequest) -> GenerateTSResponse:
    """Generate a term sheet from natural language input."""
    try:
        result = await generate_term_sheet(request.nl_input)
        return GenerateTSResponse(
            term_sheet=result["term_sheet"],
            deal_config=result["deal_config"],
            validation_errors=result["validation_errors"],
            clarification_questions=result["clarification_questions"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

