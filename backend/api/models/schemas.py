from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    mime: Optional[str] = None
    blob_path: str
    status: Optional[str] = None
    leverage_json: dict
    graph_json: Optional[dict] = None
    pages_json: Optional[dict] = None


class ClauseOut(BaseModel):
    id: str
    document_id: str
    clause_key: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    page_hint: Optional[int] = None


class AnalysisOut(BaseModel):
    id: str
    clause_id: str
    band_name: Optional[str] = None
    band_score: Optional[float] = None
    analysis_json: Optional[dict[str, Any]] = None
    redraft_text: Optional[str] = None


