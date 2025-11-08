from __future__ import annotations

import io
from typing import Dict, List

from pdfminer.high_level import extract_text


def _paragraphs_from_text(text: str) -> List[str]:
    blocks = [b.strip() for b in text.split("\n\n")]
    return [b for b in blocks if b]


def build_html_with_spans(paragraphs: List[str]) -> str:
    parts: List[str] = ["<div class=\"page\">"]
    for idx, para in enumerate(paragraphs):
        span_id = f"clause-{idx}"
        parts.append(f"<p><span id=\"{span_id}\">{para}</span></p>")
    parts.append("</div>")
    return "".join(parts)


def parse_pdf_bytes(file_bytes: bytes) -> Dict:
    text = extract_text(io.BytesIO(file_bytes)) or ""
    paragraphs = _paragraphs_from_text(text)
    html = build_html_with_spans(paragraphs)
    pages_json = {"pages": [{"index": 0, "html": html}]}
    return {
        "text_plain": text,
        "pages_json": pages_json,
    }


