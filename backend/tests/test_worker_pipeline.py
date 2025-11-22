import json
from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, JSON, String, Table, Text, MetaData, text, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.core.settings import settings
from api.core.db import schema_table
from api.services import supabase_client
from api.workers import handlers


@pytest_asyncio.fixture
async def sqlite_session(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    metadata = MetaData()

    def _register_functions(dbapi_conn, _):
        dbapi_conn.create_function("gen_random_uuid", 0, lambda: str(uuid4()))
        dbapi_conn.create_function("now", 0, lambda: datetime.utcnow().isoformat())

    event.listen(engine.sync_engine, "connect", _register_functions)

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                create table if not exists documents (
                    id text primary key,
                    user_id text not null,
                    filename text not null,
                    mime text,
                    blob_path text not null,
                    pages_json json,
                    text_plain text,
                    graph_json json,
                    leverage_json json not null default ('{"investor": 0.6, "founder": 0.4}'),
                    checksum text,
                    status text not null default 'uploaded',
                    created_at text not null default (datetime('now'))
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                create table if not exists clauses (
                    id text primary key,
                    document_id text not null,
                    clause_key text,
                    title text,
                    text text,
                    start_idx integer,
                    end_idx integer,
                    page_hint integer,
                    band_key text,
                    score real,
                    json_meta json,
                    created_at text not null default (datetime('now'))
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                create table if not exists analyses (
                    id text primary key,
                    document_id text not null,
                    clause_id text not null,
                    band_name text,
                    band_score real,
                    inputs_json json,
                    analysis_json json,
                    redraft_text text,
                    created_at text not null default (datetime('now'))
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                create table if not exists jobs (
                    id text primary key,
                    type text not null,
                    document_id text,
                    payload json,
                    status text not null,
                    attempts integer not null default 0,
                    idempotency_key text unique,
                    last_error text,
                    failed_at text,
                    created_at text not null default (datetime('now')),
                    updated_at text not null default (datetime('now'))
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                create table if not exists chunks (
                    id text primary key,
                    document_id text not null,
                    clause_id text,
                    block_id text not null,
                    page integer not null,
                    kind text not null,
                    text text not null,
                    meta json not null default ('{}'),
                    created_at text not null default (datetime('now'))
                )
                """
            )
        )
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(supabase_client, "get_sessionmaker", lambda: SessionLocal)
    monkeypatch.setattr(handlers, "get_sessionmaker", lambda: SessionLocal)
    monkeypatch.setattr(settings, "DB_SCHEMA", "")
    yield SessionLocal
    await engine.dispose()


@pytest.mark.asyncio
async def test_worker_pipeline_sequence(monkeypatch, sqlite_session):
    SessionLocal = sqlite_session
    monkeypatch.setattr(settings, "EMBEDDINGS_ENABLED", False)

    async def fake_download(*_):
        return b"dummy"

    monkeypatch.setattr(supabase_client, "download_file", fake_download)
    monkeypatch.setattr(handlers, "download_file", fake_download)

    import api.services.parse_docling as parse_docling
    import api.services.parse_pdf as parse_pdf
    import api.services.parse_docx as parse_docx
    import api.services.chunking as chunking
    import api.services.embedder as embedder
    import api.services.extract_regex as extract_regex
    import api.services.extract_llm as extract_llm
    import api.services.build_graph as build_graph
    import api.services.events as events

    monkeypatch.setattr(
        parse_docling,
        "parse_with_docling",
        lambda _: {
            "html_pages": ["<p>x</p>"],
            "blocks": [{"block_id": "block-1", "page": 0, "text": "Clause text"}],
            "parser": {"engine": "docling"},
            "text_plain": "Clause text",  # Include text_plain for fallback extraction
        },
    )
    monkeypatch.setattr(parse_pdf, "parse_pdf_bytes", lambda _: {"pages": [], "text_plain": "Clause text"})
    monkeypatch.setattr(parse_docx, "parse_docx_bytes", lambda _: {"pages": [], "text_plain": "Clause text"})
    def mock_chunks_from_pages_json(pages_json):
        # Always return a chunk with a valid block_id
        return [
            {"block_id": "block-1", "page": 0, "kind": "para", "text": "Clause text", "meta": {}}
        ]
    # Mock both the module function and the imported function in handlers
    monkeypatch.setattr(chunking, "chunks_from_pages_json", mock_chunks_from_pages_json)
    monkeypatch.setattr(handlers, "chunks_from_pages_json", mock_chunks_from_pages_json)
    monkeypatch.setattr(embedder, "embed_texts", lambda texts: [])
    def mock_regex_extract_from_docling(pages_json):
        # Handle both dict and JSON string inputs
        if isinstance(pages_json, str):
            try:
                import json
                pages_json = json.loads(pages_json)
            except:
                return []
        # Always return snippets if pages_json has blocks
        if isinstance(pages_json, dict) and pages_json.get("blocks"):
            return [
                {
                    "clause_key": "clause:1",
                    "title": "Clause 1",
                    "text": "Clause text",
                    "start_idx": 0,
                    "end_idx": 11,
                    "page_hint": 0,
                    "block_ids": ["block-1"],
                    "json_meta": {},
                }
            ]
        return []
    monkeypatch.setattr(extract_regex, "regex_extract_from_docling", mock_regex_extract_from_docling)
    def mock_regex_extract_plaintext(text):
        # Return snippets if text is provided
        if text and text.strip():
            return [
                {
                    "clause_key": "clause:1",
                    "title": "Clause 1",
                    "text": text[:100] if len(text) > 100 else text,
                    "start_idx": 0,
                    "end_idx": len(text),
                    "page_hint": None,
                    "block_ids": [],
                    "json_meta": {},
                }
            ]
        return []
    monkeypatch.setattr(extract_regex, "regex_extract_plaintext", mock_regex_extract_plaintext)
    monkeypatch.setattr(
        extract_llm,
        "normalize_snippets",
        lambda snippets, temperature=0.0: [
            {**snippet, "json_meta": snippet.get("json_meta", {})} for snippet in snippets
        ],
    )
    monkeypatch.setattr(build_graph, "build_graph", lambda doc_id, clause_nodes: {"nodes": clause_nodes})
    monkeypatch.setattr(events, "fire_event", lambda *args, **kwargs: None)

    document_id = str(uuid4())
    payload = {"mime": "application/pdf", "blob_path": "bucket/doc.pdf"}
    documents_table = schema_table("documents")

    async with SessionLocal() as session:
        await session.execute(
            text(
                f"""
                insert into {documents_table} (id, user_id, filename, mime, blob_path, status, leverage_json, created_at)
                values (:id, :uid, :filename, :mime, :blob, 'uploaded', :leverage_json, datetime('now'))
                """
            ),
            {
                "id": document_id,
                "uid": settings.DEMO_USER_ID,
                "filename": "test.pdf",
                "mime": payload["mime"],
                "blob": payload["blob_path"],
                "leverage_json": json.dumps({"investor": 0.6, "founder": 0.4}),
            },
        )
        await session.commit()

    parse_job = {"id": str(uuid4()), "document_id": document_id, "payload": payload}
    await handlers.handle_parse_doc(parse_job)

    # Ensure text_plain is set for extraction (handler sets it to "" for docling)
    async with SessionLocal() as session:
        await session.execute(
            text(f"update {documents_table} set text_plain = :text where id = :id"),
            {"id": document_id, "text": "Clause text"},
        )
        await session.commit()

    chunk_job = {"id": str(uuid4()), "document_id": document_id}
    await handlers.handle_chunk_embed(chunk_job)

    extract_job = {"id": str(uuid4()), "document_id": document_id}
    await handlers.handle_extract_normalize(extract_job)

    band_job = {"id": str(uuid4()), "document_id": document_id}
    await handlers.handle_band_map_graph(band_job)

    analyze_job = {"id": str(uuid4()), "document_id": document_id}
    await handlers.handle_analyze(analyze_job)

    clauses_table = schema_table("clauses")
    analyses_table = schema_table("analyses")

    async with SessionLocal() as session:
        doc_row = (
            await session.execute(
                text(f"select status from {documents_table} where id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        clause_count = (
            await session.execute(
                text(f"select count(*) as cnt from {clauses_table} where document_id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
        analysis_count = (
            await session.execute(
                text(f"select count(*) as cnt from {analyses_table} where document_id = :id"),
                {"id": document_id},
            )
        ).mappings().first()
    assert doc_row and doc_row["status"] == "analyzed"
    assert clause_count and clause_count["cnt"] > 0
    assert analysis_count and analysis_count["cnt"] > 0

