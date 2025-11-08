from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import bindparam

from api.core.settings import get_demo_user_id
from api.services.parse_pdf import parse_pdf_bytes
from api.services.parse_docx import parse_docx_bytes
from api.services.extract_regex import regex_extract
from api.services.extract_llm import normalize_snippets
from api.services.build_graph import build_graph
from api.services.supabase_client import get_sessionmaker, upload_file


router = APIRouter()


@router.options("/upload")
async def upload_options() -> dict[str, Any]:
    return {"ok": True}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    suffix = Path(file.filename or "").suffix.lower()

    is_pdf = content_type == "application/pdf" or suffix == ".pdf"
    is_docx = (
        suffix in (".docx", ".doc")
        or "wordprocessingml" in content_type
        or content_type == "application/msword"
    )

    if not (is_pdf or is_docx):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    demo_user = get_demo_user_id()
    document_id = str(uuid.uuid4())
    blob_path = f"documents/{demo_user}/{document_id}/{file.filename}"

    # Upload to Supabase Storage (dev fallback errors surface as 500 with guidance)
    try:
        await upload_file("documents", blob_path, content, content_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Storage not configured: {exc}") from exc

    # Parse to HTML/text
    try:
        if is_pdf and not is_docx:
            parsed = parse_pdf_bytes(content)
        else:
            parsed = parse_docx_bytes(content)
    except Exception as exc:  # pragma: no cover - surface friendly error to client
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {exc}") from exc

    # Extract clauses
    snippets = regex_extract(parsed.get("text_plain", ""))
    normalized = normalize_snippets(snippets)

    try:
        S = get_sessionmaker()
        async with S() as session:  # type: AsyncSession
            await _insert_document(session, document_id, demo_user, file.filename, content_type, blob_path, parsed)
            clause_ids = await _insert_clauses(session, document_id, normalized)
            # Build graph
            clause_nodes = [
                {"id": cid, "title": s.get("title"), "clause_key": s.get("clause_key")}
                for cid, s in zip(clause_ids, normalized)
            ]
            graph = build_graph(document_id, clause_nodes)
            await _update_graph(session, document_id, graph)
            await session.commit()
    except Exception as exc:  # surface as JSON error for the client
        raise HTTPException(status_code=500, detail=f"Failed to save document: {exc}") from exc

    return {"document_id": document_id}


async def _insert_document(
    session: AsyncSession,
    document_id: str,
    user_id: str,
    filename: str,
    mime: str,
    blob_path: str,
    parsed: dict,
) -> None:
    q = (
        text(
            """
            insert into public.documents (id, user_id, filename, mime, blob_path, text_plain, pages_json)
            values (:id, :user_id, :filename, :mime, :blob_path, :text_plain, :pages_json)
            on conflict (id) do nothing
            """
        )
        .bindparams(bindparam("pages_json", type_=JSONB))
    )
    await session.execute(
        q,
        {
            "id": document_id,
            "user_id": user_id,
            "filename": filename,
            "mime": mime,
            "blob_path": blob_path,
            "text_plain": parsed.get("text_plain", ""),
            "pages_json": parsed.get("pages_json", {}),
        },
    )


async def _insert_clauses(session: AsyncSession, document_id: str, normalized: list[dict]) -> list[str]:
    ids: list[str] = []
    for s in normalized:
        cid = str(uuid.uuid4())
        ids.append(cid)
        q = text(
            """
            insert into public.clauses (id, document_id, clause_key, title, text, start_idx, end_idx, page_hint)
            values (:id, :document_id, :clause_key, :title, :text, :start_idx, :end_idx, :page_hint)
            """
        )
        await session.execute(
            q,
            {
                "id": cid,
                "document_id": document_id,
                "clause_key": s.get("clause_key"),
                "title": s.get("title"),
                "text": s.get("text"),
                "start_idx": s.get("start_idx"),
                "end_idx": s.get("end_idx"),
                "page_hint": s.get("page_hint"),
            },
        )
    return ids


async def _update_graph(session: AsyncSession, document_id: str, graph: dict) -> None:
    q = (
        text("update public.documents set graph_json = :g where id = :id")
        .bindparams(bindparam("g", type_=JSONB))
    )
    await session.execute(q, {"g": graph, "id": document_id})


