from __future__ import annotations

import json
import mimetypes
import hashlib
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import bindparam

from api.core.settings import get_demo_user_id
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

    # Size cap: 25 MB
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (25MB max)")

    checksum = hashlib.sha256(content).hexdigest()
    demo_user = get_demo_user_id()

    # Short-circuit on (user_id, checksum)
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        existing = await session.execute(
            text(
                """
                select id from public.documents
                where user_id = :uid and checksum = :cs
                limit 1
                """
            ),
            {"uid": demo_user, "cs": checksum},
        )
        row = existing.mappings().first()
        if row:
            return {"document_id": row["id"]}

    # If new, create document row and upload blob, then enqueue PARSE_DOC
    document_id = str(uuid.uuid4())
    blob_path = f"{demo_user}/{document_id}/{file.filename}"
    try:
        await upload_file("documents", blob_path, content, content_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Storage not configured: {exc}") from exc

    async with S() as session:  # type: AsyncSession
        await _insert_document_min(session, document_id, demo_user, file.filename, content_type, blob_path, checksum)
        await _enqueue_job(
            session,
            job_type="PARSE_DOC",
            document_id=document_id,
            payload={"mime": content_type, "blob_path": blob_path},
            idempotency_key=f"parse::{document_id}::{checksum}",
        )
        await session.commit()

    return {"document_id": document_id}


async def _insert_document_min(
    session: AsyncSession,
    document_id: str,
    user_id: str,
    filename: str,
    mime: str,
    blob_path: str,
    checksum: str,
) -> None:
    q = (
        text(
            """
            insert into public.documents (id, user_id, filename, mime, blob_path, checksum, status)
            values (:id, :user_id, :filename, :mime, :blob_path, :checksum, 'uploaded')
            on conflict (id) do nothing
            """
        )
    )
    await session.execute(
        q,
        {
            "id": document_id,
            "user_id": user_id,
            "filename": filename,
            "mime": mime,
            "blob_path": blob_path,
            "checksum": checksum,
        },
    )


async def _enqueue_job(
    session: AsyncSession,
    job_type: str,
    document_id: str | None,
    payload: dict[str, Any],
    idempotency_key: str | None = None,
) -> None:
    import json

    payload_serializable = json.loads(json.dumps(payload, default=str))
    q = text(
        """
        insert into public.jobs (type, document_id, payload, idempotency_key, status)
        values (:type, :document_id, :payload, :idem, 'queued')
        on conflict (idempotency_key) do nothing
        """
    ).bindparams(bindparam("payload", type_=JSONB))
    await session.execute(
        q,
        {
            "type": job_type,
            "document_id": document_id,
            "payload": payload_serializable,
            "idem": idempotency_key,
        },
    )


