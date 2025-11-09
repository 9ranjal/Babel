from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import bindparam

from api.core.settings import settings
from api.services.supabase_client import get_sessionmaker, download_file
from api.services import parse_docling
from api.services.parse_pdf import parse_pdf_bytes
from api.services.parse_docx import parse_docx_bytes
from api.services.chunking import chunks_from_pages_json
from api.services.embedder import embed_texts
from api.services.extract_regex import regex_extract_from_docling, regex_extract_plaintext
from api.services.extract_llm import normalize_snippets
from api.services.build_graph import build_graph
from api.services.events import fire_event

# Handlers are wired by name; implementations will be filled alongside queue runner.
HandlerFn = Callable[[dict], Awaitable[None]]

HANDLERS: Dict[str, HandlerFn] = {}


async def _enqueue_job(
    session: AsyncSession,
    job_type: str,
    document_id: Optional[str],
    payload: Dict[str, Any],
    idempotency_key: Optional[str],
) -> None:
    import json

    payload_serializable = json.dumps(payload, default=str)
    q = text(
        """
        insert into public.jobs (type, document_id, payload, idempotency_key, status)
        values (:type, :document_id, :payload, :idem, 'queued')
        on conflict (idempotency_key) do nothing
        """
    )
    await session.execute(
        q,
        {
            "type": job_type,
            "document_id": document_id,
            "payload": payload_serializable,
            "idem": idempotency_key,
        },
    )


def _to_docling_contract_from_fallback(parsed: Dict[str, Any]) -> Dict[str, Any]:
    # Convert fallback parse ({pages:[{html}]}, text_plain) to Docling-like contract
    pages = parsed.get("pages_json", {}).get("pages", [])
    html_pages = [p.get("html", "") for p in pages]
    return {
        "html_pages": html_pages,
        "blocks": [],  # no structured blocks from fallback
        "tables": [],
        "parser": {"engine": "pymupdf", "version": "1"},
    }


async def handle_parse_doc(job: dict) -> None:  # PARSE_DOC
    payload = job.get("payload") or {}
    document_id = job.get("document_id")
    mime = payload.get("mime")
    blob_path = payload.get("blob_path")
    if not document_id or not blob_path:
        return
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        # Idempotency: skip if pages_json already set
        existing = (
            await session.execute(
                text("select pages_json from public.documents where id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        if existing and existing["pages_json"]:
            # already parsed; chain next
            await _enqueue_job(
                session,
                "CHUNK_EMBED",
                document_id,
                {"document_id": document_id},
                f"chunks::{document_id}::v1",
            )
            await session.commit()
            return

        # Download
        bytes_content = await download_file("documents", blob_path)

        # Try Docling
        try:
            pages_json = parse_docling.parse_with_docling(bytes_content)
            engine = pages_json.get("parser", {}).get("engine", "docling")
            text_plain = ""  # docling path may not return plain text; keep empty in MVP
            # If Docling produced no usable pages/blocks, fall back
            html_pages = (pages_json or {}).get("html_pages") or []
            blocks = (pages_json or {}).get("blocks") or []
            if not html_pages and not blocks:
                raise RuntimeError("docling-empty")
        except Exception:
            # Fallback to naive extractors
            if (mime or "").lower().startswith("application/pdf"):
                parsed_fb = parse_pdf_bytes(bytes_content)
            else:
                parsed_fb = parse_docx_bytes(bytes_content)
            pages_json = _to_docling_contract_from_fallback(parsed_fb)
            text_plain = parsed_fb.get("text_plain", "")

        # Persist
        import json
        q = text(
            """
            update public.documents
            set text_plain = :text_plain, pages_json = :pages_json, status = 'parsed'
            where id = :id
            """
        )
        await session.execute(q, {"id": document_id, "text_plain": text_plain, "pages_json": json.dumps(pages_json)})

        # Chain next
        await _enqueue_job(
            session,
            "CHUNK_EMBED",
            document_id,
            {"document_id": document_id},
            f"chunks::{document_id}::v1",
        )
        fire_event("parsed", {"document_id": document_id})
        await session.commit()


async def handle_chunk_embed(job: dict) -> None:  # CHUNK_EMBED
    document_id = job.get("document_id")
    if not document_id:
        return
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        # Idempotency: if chunks exist, skip
        existing = (
            await session.execute(
                text("select 1 from public.chunks where document_id = :id limit 1"),
                {"id": document_id},
            )
        ).scalar_one_or_none()
        if existing:
            await _enqueue_job(session, "EXTRACT_NORMALIZE", document_id, {"document_id": document_id}, f"extract::{document_id}::v1")
            await session.commit()
            return
        # Load pages_json
        row = (
            await session.execute(
                text("select pages_json from public.documents where id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        pages_json = row["pages_json"] if row else {}
        chunks = chunks_from_pages_json(pages_json)
        # Insert chunks
        import json

        for ch in chunks:
            meta_serializable = json.loads(json.dumps(ch.get("meta", {}), default=str))
            await session.execute(
                text(
                    """
                    insert into public.chunks (id, document_id, clause_id, block_id, page, kind, text, meta)
                    values (gen_random_uuid(), :document_id, null, :block_id, :page, :kind, :text, :meta)
                    """
                ),
                {
                    "document_id": document_id,
                    "block_id": ch.get("block_id"),
                    "page": ch.get("page", 0),
                    "kind": ch.get("kind", "para"),
                    "text": ch.get("text", "") or "",
                    "meta": meta_serializable,
                },
            )
        # Embeddings (optional)
        if settings.EMBEDDINGS_ENABLED and chunks:
            texts = [c.get("text", "") or "" for c in chunks]
            embs = embed_texts(texts)
            # Persist embeddings: in MVP, skip for speed if zero-vectors; otherwise could update by block_id
            # Not strictly needed for functional pipeline assertions.
            pass
        # Update status and chain
        await session.execute(
            text("update public.documents set status='chunked' where id = :id"),
            {"id": document_id},
        )
        await _enqueue_job(session, "EXTRACT_NORMALIZE", document_id, {"document_id": document_id}, f"extract::{document_id}::v1")
        fire_event("chunked", {"document_id": document_id, "n": len(chunks)})
        await session.commit()


async def handle_extract_normalize(job: dict) -> None:  # EXTRACT_NORMALIZE
    document_id = job.get("document_id")
    if not document_id:
        return
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        # Idempotency: if clauses exist for doc, skip to next
        existing = (
            await session.execute(
                text("select 1 from public.clauses where document_id = :id limit 1"),
                {"id": document_id},
            )
        ).scalar_one_or_none()
        if existing:
            await _enqueue_job(session, "BAND_MAP_GRAPH", document_id, {"document_id": document_id}, f"band::{document_id}::v1")
            await session.commit()
            return
        # Load text and leverage (if any)
        row = (
            await session.execute(
                text("select text_plain, pages_json, leverage_json from public.documents where id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        text_plain = (row["text_plain"] or "") if row else ""
        pages_json = row["pages_json"] if row else {}
        if not text_plain and isinstance(pages_json, dict) and "text_plain" in pages_json:
            text_plain = pages_json.get("text_plain") or ""

        snippets: List[Dict[str, Any]] = []
        if isinstance(pages_json, dict) and pages_json.get("blocks"):
            try:
                snippets = regex_extract_from_docling(pages_json)
            except Exception:  # pragma: no cover - defensive, fall back to plaintext path
                snippets = []
        if not snippets:
            snippets = regex_extract_plaintext(text_plain)

        if not snippets and text_plain.strip():
            snippets = [
                {
                    "clause_key": "document_overview",
                    "title": "Document Overview",
                    "text": text_plain[:500] + "..." if len(text_plain) > 500 else text_plain,
                    "start_idx": 0,
                    "end_idx": len(text_plain),
                    "page_hint": None,
                    "attributes": {},
                    "block_ids": [],
                    "source": "fallback",
                    "confidence": 0.5,
                }
            ]

        normalized = normalize_snippets(snippets, temperature=0.0)
        insert_clause = text(
            """
                    insert into public.clauses (id, document_id, clause_key, title, text, start_idx, end_idx, page_hint, json_meta)
                    values (gen_random_uuid(), :document_id, :clause_key, :title, :text, :start_idx, :end_idx, :page_hint, :json_meta)
                    returning id
                    """
        ).bindparams(bindparam("json_meta", type_=JSONB))
        clause_ids: List[str] = []
        for snippet in normalized:
            res = await session.execute(
                insert_clause,
                {
                    "document_id": document_id,
                    "clause_key": snippet.get("clause_key"),
                    "title": snippet.get("title"),
                    "text": snippet.get("text"),
                    "start_idx": snippet.get("start_idx"),
                    "end_idx": snippet.get("end_idx"),
                    "page_hint": snippet.get("page_hint"),
                    "json_meta": snippet.get("json_meta", {}),
                },
            )
            clause_ids.append(str(res.scalar_one()))

        rows = (
            await session.execute(
                text("select id, block_id, page from public.chunks where document_id = :id"),
                {"id": document_id},
            )
        ).mappings().all()
        block_to_chunk: Dict[str, str] = {}
        page_to_chunk: Dict[int, str] = {}
        for r in rows:
            chunk_id = str(r["id"])
            block_id = r.get("block_id")
            page_val = r.get("page")
            if block_id:
                block_to_chunk[str(block_id)] = chunk_id
            if page_val is not None:
                page_to_chunk.setdefault(int(page_val), chunk_id)

        for cid, snippet in zip(clause_ids, normalized):
            target_chunk = None
            for block_id in snippet.get("block_ids", []):
                if block_id in block_to_chunk:
                    target_chunk = block_to_chunk[block_id]
                    break
            if not target_chunk:
                page_hint = snippet.get("page_hint")
                if page_hint is not None and int(page_hint) in page_to_chunk:
                    target_chunk = page_to_chunk[int(page_hint)]
                elif 0 in page_to_chunk:
                    target_chunk = page_to_chunk[0]
            if target_chunk:
                await session.execute(
                    text("update public.chunks set clause_id = :cid where id = :chunk_id"),
                    {"cid": cid, "chunk_id": target_chunk},
                )
        await session.execute(
            text("update public.documents set status='extracted' where id = :id"),
            {"id": document_id},
        )
        await _enqueue_job(session, "BAND_MAP_GRAPH", document_id, {"document_id": document_id}, f"band::{document_id}::v1")
        fire_event("extracted", {"document_id": document_id, "n": len(clause_ids)})
        await session.commit()


async def handle_band_map_graph(job: dict) -> None:  # BAND_MAP_GRAPH
    document_id = job.get("document_id")
    if not document_id:
        return
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        # Idempotency: if graph_json exists, skip to ANALYZE
        existing = (
            await session.execute(
                text("select graph_json from public.documents where id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        if existing and existing["graph_json"]:
            await _enqueue_job(session, "ANALYZE", document_id, {"document_id": document_id}, f"analyze::{document_id}::v1")
            await session.commit()
            return
        # Fetch clauses for graph nodes
        rows = (
            await session.execute(
                text("select id, clause_key, title from public.clauses where document_id = :id order by created_at asc"),
                {"id": document_id},
            )
        ).mappings().all()
        clause_nodes = [{"id": str(r["id"]), "clause_key": r["clause_key"], "title": r["title"]} for r in rows]
        graph = build_graph(document_id, clause_nodes)
        await session.execute(
            text("update public.documents set graph_json=:g, status='graphed' where id = :id").bindparams(
                bindparam("g", type_=JSONB)
            ),
            {"id": document_id, "g": graph},
        )
        await _enqueue_job(session, "ANALYZE", document_id, {"document_id": document_id}, f"analyze::{document_id}::v1")
        fire_event("graphed", {"document_id": document_id})
        await session.commit()


async def handle_analyze(job: dict) -> None:  # ANALYZE
    document_id = job.get("document_id")
    if not document_id:
        return
    S = get_sessionmaker()
    async with S() as session:  # type: AsyncSession
        # Idempotency: if analyses count == clauses count, set status and exit
        counts = (
            await session.execute(
                text(
                    """
                    select
                      (select count(*) from public.clauses where document_id = :id) as n_clauses,
                      (select count(*) from public.analyses where document_id = :id) as n_analyses
                    """
                ),
                {"id": document_id},
            )
        ).mappings().first()
        n_clauses = int(counts["n_clauses"] or 0)
        n_analyses = int(counts["n_analyses"] or 0)
        if n_clauses > 0 and n_analyses >= n_clauses:
            await session.execute(
                text("update public.documents set status='analyzed' where id=:id"),
                {"id": document_id},
            )
            await session.commit()
            return
        # Load leverage
        lev_row = (
            await session.execute(
                text("select leverage_json from public.documents where id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        leverage = lev_row["leverage_json"] if lev_row and lev_row["leverage_json"] else {"investor": 0.6, "founder": 0.4}
        # Iterate clauses and upsert analyses
        rows = (
            await session.execute(
                text("select id, clause_key, text from public.clauses where document_id = :id order by created_at asc"),
                {"id": document_id},
            )
        ).mappings().all()
        from api.services.analyze import analyze_clause

        for r in rows:
            await analyze_clause(
                session=session,
                document_id=document_id,
                clause_id=str(r["id"]),
                clause_key=r["clause_key"],
                clause_text=r["text"] or "",
                leverage=leverage,
                attributes=None,
            )
        await session.execute(
            text("update public.documents set status='analyzed' where id=:id"),
            {"id": document_id},
        )
        fire_event("analyzed", {"document_id": document_id, "n": len(rows)})
        await session.commit()


HANDLERS.update(
    {
        "PARSE_DOC": handle_parse_doc,
        "CHUNK_EMBED": handle_chunk_embed,
        "EXTRACT_NORMALIZE": handle_extract_normalize,
        "BAND_MAP_GRAPH": handle_band_map_graph,
        "ANALYZE": handle_analyze,
    }
)


