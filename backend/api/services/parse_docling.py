from __future__ import annotations

import io
import re
from itertools import count
from typing import Any, Dict, List, Sequence


def parse_with_docling(file_bytes: bytes) -> Dict[str, Any]:
    """
    Use Docling to parse bytes and produce the locked pages_json shape.
    Fallback behavior (handled by caller) kicks in if docling yields no pages/blocks.
    """
    try:
        # Lazy import to avoid hard dependency at import time
        from docling.document_converter import DocumentConverter  # type: ignore
        from docling_core.transforms.chunker.hierarchical_chunker import (  # type: ignore
            HierarchicalChunker,
        )
        from docling_core.types.doc.document import (  # type: ignore
            DocItemLabel,
            TableItem,
        )
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

    document = result.document

    # Prefer markdown export for stability, then convert to simple HTML for viewer
    html_pages: List[str] = []
    plain_text: str = ""
    markdown_renderer = marko.Markdown()

    def _strip_html(value: str) -> str:
        stripped = re.sub(r"<[^>]+>", " ", value)
        stripped = stripped.replace("&nbsp;", " ")
        return re.sub(r"\s+", " ", stripped).strip()

    def _markdown_to_plain(value: str) -> str:
        if not value:
            return ""
        try:
            rendered = markdown_renderer.convert(value)
        except Exception:
            rendered = value
        return _strip_html(rendered) if rendered else ""

    def _coerce_list(value: Sequence[str] | None) -> List[str]:
        return [v for v in value or [] if v]

    block_counter = count()
    processed_refs: set[str] = set()
    blocks: List[Dict[str, Any]] = []

    def _add_block(
        kind: str,
        text: str,
        *,
        doc_refs: Sequence[str] | None = None,
        extra_meta: Dict[str, Any] | None = None,
        already_clean: bool = False,
    ) -> None:
        cleaned = text if already_clean else _markdown_to_plain(text)
        if not cleaned:
            return
        meta: Dict[str, Any] = {"source": "docling"}
        refs = [ref for ref in (doc_refs or []) if ref]
        if refs:
            meta["doc_items"] = refs
        if extra_meta:
            meta.update(extra_meta)
        blocks.append(
            {
                "id": f"docling-{next(block_counter)}",
                "type": kind,
                "page": 0,
                "text": cleaned,
                "meta": meta,
            }
        )
        if refs:
            processed_refs.update(refs)

    def _looks_like_heading(text: str) -> bool:
        candidate = text.strip()
        if not candidate:
            return False
        if candidate.endswith(":"):
            return True
        words = candidate.split()
        if len(words) <= 6 and candidate.isupper():
            return True
        lowered = candidate.lower()
        return lowered in {
            "investment terms",
            "miscellaneous",
            "rights of investor and new preference shares",
        }

    def _infer_heading_from_value(value: str) -> str | None:
        lowered = value.lower()
        if "proceeds from the proposed investment" in lowered or lowered.startswith("the proceeds from the proposed investment"):
            return "Use of Proceeds:"
        return None

    def _process_table(table_item: TableItem) -> None:
        processed_refs.add(table_item.self_ref)
        dump = table_item.data.model_dump()
        grid = dump.get("grid") or []
        num_cols = dump.get("num_cols") or 0
        for row_idx, cells in enumerate(grid):
            if not cells:
                continue
            # Sort by column position
            sorted_cells = sorted(
                cells, key=lambda cell: cell.get("start_col_offset_idx", 0)
            )
            if all(cell.get("column_header") for cell in sorted_cells):
                header_text = _markdown_to_plain(sorted_cells[0].get("text", ""))
                if header_text:
                    _add_block(
                        "heading",
                        header_text,
                        doc_refs=[sorted_cells[0].get("ref") or table_item.self_ref],
                        extra_meta={"table_row": row_idx, "column": 0},
                        already_clean=True,
                    )
                continue

            if num_cols >= 2 and len(sorted_cells) >= 2:
                heading_cell, value_cell = sorted_cells[0], sorted_cells[1]
                heading_text = _markdown_to_plain(heading_cell.get("text", ""))
                value_text = _markdown_to_plain(value_cell.get("text", ""))
                if not heading_text:
                    inferred = _infer_heading_from_value(value_text)
                    if inferred:
                        heading_text = inferred
                table_ref = table_item.self_ref
                if heading_text:
                    _add_block(
                        "heading",
                        heading_text,
                        doc_refs=[heading_cell.get("ref") or table_ref],
                        extra_meta={"table_row": row_idx, "column": 0},
                        already_clean=True,
                    )
                if value_text:
                    _add_block(
                        "paragraph",
                        value_text,
                        doc_refs=[value_cell.get("ref") or table_ref],
                        extra_meta={"table_row": row_idx, "column": 1},
                        already_clean=True,
                    )
            else:
                text = _markdown_to_plain(sorted_cells[0].get("text", ""))
                if text:
                    _add_block(
                        "paragraph",
                        text,
                        doc_refs=[sorted_cells[0].get("ref") or table_item.self_ref],
                        extra_meta={"table_row": row_idx},
                        already_clean=True,
                    )

    try:
        md_text: str = document.export_to_markdown()
        html_pages = [markdown_renderer.convert(md_text)]
    except Exception:
        # As a secondary option, try plain text if markdown export is unavailable
        try:
            plain = document.export_to_text()
            # Wrap plaintext in <pre> to satisfy viewer contract
            html_pages = [f"<pre>{plain}</pre>"]
        except Exception:
            html_pages = []

    # Always try to extract plain text for downstream regex
    try:
        plain_text = document.export_to_text() or ""
    except Exception:
        if html_pages:
            # crude fallback: strip tags (basic) if text export unavailable
            import re as _re
            plain_text = _re.sub(r"<[^>]+>", " ", html_pages[0])
        else:
            plain_text = ""

    # Build layout-aware blocks leveraging Docling chunker & table metadata
    try:
        chunker = HierarchicalChunker()
        for chunk in chunker.chunk(document):
            doc_items = chunk.meta.doc_items or []
            doc_refs = [item.self_ref for item in doc_items if getattr(item, "self_ref", None)]
            if doc_refs and all(ref in processed_refs for ref in doc_refs):
                continue
            if any(item.label == DocItemLabel.TABLE for item in doc_items):
                for doc_item in doc_items:
                    if doc_item.label == DocItemLabel.TABLE and isinstance(doc_item, TableItem):
                        _process_table(doc_item)
                continue

            raw_text = chunk.text or ""
            cleaned_text = _markdown_to_plain(raw_text)
            if not cleaned_text:
                continue
            block_kind = "heading" if _looks_like_heading(cleaned_text) else "paragraph"
            extra_meta: Dict[str, Any] = {}
            headings = _coerce_list(chunk.meta.headings if chunk.meta else None)
            if headings:
                extra_meta["headings"] = headings
            _add_block(
                block_kind,
                cleaned_text,
                doc_refs=doc_refs,
                extra_meta=extra_meta,
                already_clean=True,
            )
    except Exception:
        # If chunking fails for any reason, fall back to plaintext-only block
        lone_block_text = _markdown_to_plain(plain_text) or plain_text
        if lone_block_text:
            _add_block(
                "paragraph",
                lone_block_text,
                doc_refs=[],
                already_clean=True,
            )

    pages_json: Dict[str, Any] = {
        "html_pages": html_pages,
        "blocks": blocks,
        "tables": [],
        "parser": {"engine": "docling", "version": getattr(result, "version", "unknown")},
    }
    # Add plain text alongside to let caller persist text_plain
    pages_json["text_plain"] = plain_text
    return pages_json


