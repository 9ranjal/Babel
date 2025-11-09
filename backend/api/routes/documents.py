from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.settings import get_demo_user_id
from api.models.schemas import DocumentOut, ClauseOut
from api.services.supabase_client import get_sessionmaker


router = APIRouter()


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: str) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        row = (
            await session.execute(
                text(
                    "select id, filename, mime, blob_path, status, leverage_json, graph_json, pages_json from public.documents where id = :id and user_id = :uid"
                ),
                {"id": doc_id, "uid": demo_user},
            )
        ).mappings().fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "id": str(row.id),
            "filename": row.filename,
            "mime": row.mime,
            "blob_path": row.blob_path,
            "status": row.status,
            "leverage_json": row.leverage_json,
            "graph_json": row.graph_json,
            "pages_json": row.pages_json,
        }


@router.get("/documents/{doc_id}/clauses", response_model=list[ClauseOut])
async def list_clauses(doc_id: str) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        # ensure document ownership
        owned = (
            await session.execute(
                text("select 1 from public.documents where id = :id and user_id = :uid"),
                {"id": doc_id, "uid": demo_user},
            )
        ).scalar_one_or_none()
        if not owned:
            raise HTTPException(status_code=404, detail="Not found")
        rows = (
            await session.execute(
                text(
                    "select id, document_id, clause_key, title, text, page_hint from public.clauses where document_id = :id order by created_at asc"
                ),
                {"id": doc_id},
            )
        ).mappings().fetchall()
        return [
            {
                "id": str(r.id),
                "document_id": str(r.document_id),
                "clause_key": r.clause_key,
                "title": r.title,
                "text": r.text,
                "page_hint": r.page_hint,
            }
            for r in rows
        ]


@router.get("/documents/{doc_id}/status")
async def get_document_status(doc_id: str) -> Any:
    demo_user = get_demo_user_id()
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        row = (
            await session.execute(
                text(
                    "select status from public.documents where id = :id and user_id = :uid"
                ),
                {"id": doc_id, "uid": demo_user},
            )
        ).mappings().fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": row.status}


