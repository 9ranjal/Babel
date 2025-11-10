from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import bindparam
import json

from api.core.settings import get_demo_user_id
from api.models.schemas import DocumentOut, ClauseOut
from api.services.supabase_client import get_sessionmaker
from api.core.logging import logger


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
        pages_json = row.pages_json
        if isinstance(pages_json, str):
            try:
                pages_json = json.loads(pages_json)
            except json.JSONDecodeError:
                pages_json = None
        graph_json = row.graph_json
        if isinstance(graph_json, str):
            try:
                graph_json = json.loads(graph_json)
            except json.JSONDecodeError:
                graph_json = None
        logger.info("get_document doc_id=%s status=%s", doc_id, row.status)
        return {
            "id": str(row.id),
            "filename": row.filename,
            "mime": row.mime,
            "blob_path": row.blob_path,
            "status": row.status,
            "leverage_json": row.leverage_json,
            "graph_json": graph_json,
            "pages_json": pages_json,
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
            logger.warning("list_clauses denied doc_id=%s not owned by demo user", doc_id)
            raise HTTPException(status_code=404, detail="Not found")
        rows = (
            await session.execute(
                text(
                    "select id, document_id, clause_key, title, text, page_hint from public.clauses where document_id = :id order by created_at asc"
                ),
                {"id": doc_id},
            )
        ).mappings().fetchall()
        logger.info("list_clauses doc_id=%s returned=%d", doc_id, len(rows))
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
                    "select id, status, mime, blob_path, checksum from public.documents where id = :id and user_id = :uid"
                ),
                {"id": doc_id, "uid": demo_user},
            )
        ).mappings().fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        status = row["status"]
        # Auto-heal: if doc is 'uploaded' and no queued/working job exists, requeue parse idempotently
        if status == "uploaded":
            j = (
                await session.execute(
                    text("select 1 from public.jobs where document_id = :doc and status in ('queued','working') limit 1"),
                    {"doc": doc_id},
                )
            ).first()
            if j is None:
                payload = {"mime": row["mime"], "blob_path": row["blob_path"]}
                insert_job = text(
                    """
                    insert into public.jobs (type, document_id, payload, status, attempts, idempotency_key)
                    values (:type, :doc, :payload, 'queued', 0, :idem)
                    on conflict (idempotency_key) do update
                    set status = 'queued',
                        attempts = 0,
                        last_error = null,
                        failed_at = null,
                        payload = excluded.payload,
                        document_id = excluded.document_id,
                        type = excluded.type,
                        updated_at = now()
                    """
                ).bindparams(bindparam("payload", type_=JSONB))
                idem_key = f"parse::{doc_id}::{row['checksum']}"
                await session.execute(
                    insert_job,
                    {
                        "type": "PARSE_DOC",
                        "doc": doc_id,
                        "payload": json.loads(json.dumps(payload, default=str)),
                        "idem": idem_key,
                    },
                )
                await session.commit()
                logger.info("status auto-requeue doc_id=%s idem=%s", doc_id, idem_key)
        logger.info("get_document_status doc_id=%s status=%s", doc_id, status)
        return {"status": status}


