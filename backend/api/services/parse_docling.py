from __future__ import annotations

import io
from typing import Any, Dict, List


def parse_with_docling(file_bytes: bytes) -> Dict[str, Any]:
    """
    Use Docling to parse bytes and produce the locked pages_json shape.
    Fallback behavior (handled by caller) kicks in if docling yields no pages/blocks.
    """
    try:
        # Lazy import to avoid hard dependency at import time
        from docling.document_converter import DocumentConverter  # type: ignore
        import marko  # lightweight md->html converter (already a transitive dep)
    except Exception as exc:  # pragma: no cover
        # Surface an exception so caller can fallback to other parsers
        raise RuntimeError(f"Docling not available: {exc}") from exc

    converter = DocumentConverter()
    # Docling prefers a file path or structured stream; write to temp file for reliability.
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".bin") as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        result = converter.convert(tmp.name)

    # Prefer markdown export for stability, then convert to simple HTML for viewer
    html_pages: List[str] = []
    plain_text: str = ""
    try:
        md_text: str = result.document.export_to_markdown()
        html_pages = [marko.convert(md_text)]
    except Exception:
        # As a secondary option, try plain text if markdown export is unavailable
        try:
            plain = result.document.export_to_text()
            # Wrap plaintext in <pre> to satisfy viewer contract
            html_pages = [f"<pre>{plain}</pre>"]
        except Exception:
            html_pages = []

    # Always try to extract plain text for downstream regex
    try:
        plain_text = result.document.export_to_text() or ""
    except Exception:
        if html_pages:
            # crude fallback: strip tags (basic) if text export unavailable
            import re as _re
            plain_text = _re.sub(r"<[^>]+>", " ", html_pages[0])
        else:
            plain_text = ""

    # We are not attempting to synthesize 'blocks' from Docling's internals yet.
    # The chunker only depends on html_pages + blocks; blocks can be empty.
    pages_json: Dict[str, Any] = {
        "html_pages": html_pages,
        "blocks": [],
        "tables": [],
        "parser": {"engine": "docling", "version": getattr(result, "version", "unknown")},
    }
    # Add plain text alongside to let caller persist text_plain
    pages_json["text_plain"] = plain_text
    return pages_json


