from __future__ import annotations

from typing import Any, Dict, List


def chunks_from_pages_json(pages_json: Dict[str, Any]) -> List[dict]:
    """
    Build chunks strictly from pages_json['blocks'] and pages_json['html_pages'].
    This function MUST NOT re-read or re-parse the original PDF/DOCX.
    """
    blocks = pages_json.get("blocks", []) or []
    html_pages = pages_json.get("html_pages", []) or []

    chunks: List[dict] = []
    # Preferred path: use structured blocks if provided
    for b in blocks:
        chunks.append(
            {
                "block_id": b.get("id"),
                "page": int(b.get("page", 0)),
                "kind": str(b.get("type", "para")),
                "text": (b.get("text") or "").strip(),  # optional field if present
                "meta": {"bbox": b.get("bbox"), "source": "docling"},
            }
        )
    if chunks:
        return chunks

    # Fallback: derive paragraph chunks from HTML pages when no blocks were provided
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except Exception:
        BeautifulSoup = None  # type: ignore

    for page_index, html in enumerate(html_pages):
        if not html:
            continue
        paras: List[str] = []
        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            for p in soup.find_all("p"):
                text = (p.get_text(separator=" ", strip=True) or "").strip()
                if text:
                    paras.append(text)
        else:
            # Very crude fallback: split on paragraph tags
            import re as _re

            for m in _re.finditer(r"<p[^>]*>(.*?)</p>", html, flags=_re.IGNORECASE | _re.DOTALL):
                text = _re.sub(r"<[^>]+>", " ", m.group(1)).strip()
                text = " ".join(text.split())
                if text:
                    paras.append(text)

        for i, para in enumerate(paras):
            chunks.append(
                {
                    "block_id": f"p-{page_index}-{i}",
                    "page": page_index,
                    "kind": "para",
                    "text": para,
                    "meta": {"source": "html_fallback"},
                }
            )
    return chunks


