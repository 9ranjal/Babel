from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.db import schema_table
from api.core.settings import get_demo_user_id
from api.models.schemas import ClauseOut, AnalysisOut
from api.services.analyze import analyze_clause
from api.services.redraft import save_redraft
from api.services.supabase_client import get_sessionmaker


router = APIRouter()


async def _get_clause_with_doc(session: AsyncSession, clause_id: str, demo_user: str):
    clauses_table = schema_table("clauses")
    documents_table = schema_table("documents")
    q = text(
        f"""
        select c.id as clause_id, c.document_id, c.clause_key, c.title, c.text, d.leverage_json
        from {clauses_table} c
        join {documents_table} d on d.id = c.document_id
        where c.id = :cid and d.user_id = :uid
        """
    )
    return (await session.execute(q, {"cid": clause_id, "uid": demo_user})).mappings().fetchone()


@router.get("/clauses/{clause_id}", response_model=ClauseOut)
async def get_clause(clause_id: str) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        row = await _get_clause_with_doc(session, clause_id, demo_user)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "id": str(row.clause_id),
            "document_id": str(row.document_id),
            "clause_key": row.clause_key,
            "title": row.title,
            "text": row.text,
            "page_hint": None,
        }


@router.post("/clauses/{clause_id}/analyze", response_model=AnalysisOut)
async def analyze(clause_id: str, reasoned: bool = False) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        row = await _get_clause_with_doc(session, clause_id, demo_user)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")

        if reasoned:
            # Use copilot for reasoned analysis
            from ..services.copilot_service import copilot_service
            from ..services.extract_regex import extract_attributes

            # Get clause attributes
            derived_attrs = extract_attributes(row.text or "")

            # Get reasoned analysis from copilot
            reasoned_analysis = await copilot_service.analyze_clause(
                clause_key=row.clause_key or "",
                clause_title=row.title or row.clause_key or "Unknown Clause",
                clause_text=row.text or "",
                attributes=derived_attrs,
                leverage=row.leverage_json or {"investor": 0.6, "founder": 0.4}
            )

            # Still do deterministic analysis for band data, but use reasoned analysis
            result = await analyze_clause(
                session,
                document_id=str(row.document_id),
                clause_id=str(row.clause_id),
                clause_key=row.clause_key,
                clause_text=row.text or "",
                leverage=row.leverage_json or {"investor": 0.6, "founder": 0.4},
                attributes={},
            )

            # Override the analysis_json with reasoned analysis
            result["analysis_json"] = {
                "posture": result.get("posture", "market"),
                "band_name": result.get("band_name"),
                "band_score": result.get("band_score"),
                "rationale": [f"AI Analysis: {reasoned_analysis[:200]}..."],
                "recommendation": reasoned_analysis,
                "trades": result["analysis_json"].get("trades", [])
            }

        else:
            # Use deterministic analysis
            result = await analyze_clause(
            session,
            document_id=str(row.document_id),
            clause_id=str(row.clause_id),
            clause_key=row.clause_key,
            clause_text=row.text or "",
            leverage=row.leverage_json or {"investor": 0.6, "founder": 0.4},
            attributes={},
        )

        await session.commit()
        return result


@router.post("/clauses/{clause_id}/redraft", response_model=AnalysisOut)
async def redraft(clause_id: str) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        row = await _get_clause_with_doc(session, clause_id, demo_user)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        result = await save_redraft(
            session,
            document_id=str(row.document_id),
            clause_id=str(row.clause_id),
            original_text=row.text or "",
        )
        await session.commit()
        return result


