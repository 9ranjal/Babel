from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.settings import get_demo_user_id
from api.models.schemas import ClauseOut, AnalysisOut
from api.services.analyze import analyze_clause
from api.services.redraft import save_redraft
from api.services.supabase_client import get_sessionmaker


router = APIRouter()


async def _get_clause_with_doc(session: AsyncSession, clause_id: str, demo_user: str):
    q = text(
        """
        select c.id as clause_id, c.document_id, c.clause_key, c.title, c.text, d.leverage_json
        from public.clauses c
        join public.documents d on d.id = c.document_id
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
async def analyze(clause_id: str) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        row = await _get_clause_with_doc(session, clause_id, demo_user)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
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


