from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Tuple

# Prefer local imports; assumes running from repo root with PYTHONPATH=.
from backend.api.services.parse_pdf import parse_pdf_bytes
from backend.api.services.parse_docx import parse_docx_bytes
from backend.api.services import parse_docling
from backend.api.services.extract_regex import (
    regex_extract_from_docling,
    regex_extract_plaintext,
)


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _extract_for_path(path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns (snippets, meta) where snippets are extracted clause snippets,
    meta includes parser info and any errors.
    """
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    meta: Dict[str, Any] = {"file": path, "ext": ext, "parser": None, "error": None}
    try:
        b = _read_bytes(path)
        snippets: List[Dict[str, Any]] = []
        if ext in (".pdf",):
            parsed = parse_pdf_bytes(b)
            meta["parser"] = "pdf"
            text_plain = parsed.get("text_plain") or ""
            if text_plain:
                snippets = regex_extract_plaintext(text_plain)
        elif ext in (".docx",):
            parsed = parse_docx_bytes(b)
            meta["parser"] = "docx"
            text_plain = parsed.get("text_plain") or ""
            if text_plain:
                snippets = regex_extract_plaintext(text_plain)
        else:
            # Attempt Docling (best-effort)
            try:
                pages_json = parse_docling.parse_with_docling(b)
                meta["parser"] = "docling"
                if (pages_json or {}).get("blocks"):
                    snippets = regex_extract_from_docling(pages_json)
                else:
                    text_plain = pages_json.get("text_plain") or ""
                    if text_plain:
                        snippets = regex_extract_plaintext(text_plain)
            except Exception as exc:
                meta["parser"] = "unknown"
                meta["error"] = f"Docling parse failed: {exc}"
                snippets = []
        return snippets, meta
    except Exception as exc:
        meta["error"] = str(exc)
        return [], meta


def _summarize(snippets: List[Dict[str, Any]], limit: int = 12) -> Dict[str, Any]:
    def _attr_subset(attrs: Dict[str, Any]) -> Dict[str, Any]:
        keys = [
            "days",
            "percent",
            "percents",
            "amount",
            "currency",
            "liq_multiple",
            "participation",
            "antidilution_type",
            "pool_percent",
            "board_size",
            "investor_directors",
            "exclusivity_days",
            "redemption_after_years",
        ]
        return {k: v for k, v in (attrs or {}).items() if k in keys}

    head = []
    for s in snippets[:limit]:
        head.append(
            {
                "clause_key": s.get("clause_key"),
                "page_hint": s.get("page_hint"),
                "attributes": _attr_subset(s.get("attributes") or {}),
            }
        )
    return {"count": len(snippets), "examples": head}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/testing/run_extraction_on_docs.py <file_or_dir> [more_paths...]")
        sys.exit(2)

    targets: List[str] = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            for fn in os.listdir(arg):
                if fn.lower().endswith((".pdf", ".docx", ".doc")):
                    targets.append(os.path.join(arg, fn))
        else:
            targets.append(arg)

    results: List[Dict[str, Any]] = []
    for path in targets:
        snippets, meta = _extract_for_path(path)
        results.append(
            {
                "file": path,
                "meta": meta,
                "summary": _summarize(snippets),
            }
        )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()


