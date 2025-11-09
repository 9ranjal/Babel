from __future__ import annotations

from io import BytesIO
from typing import Dict, List

import mammoth


def _wrap_spans(html: str) -> str:
    # naive: number paragraphs and add span ids
    out: List[str] = []
    idx = 0
    i = 0
    while i < len(html):
        pstart = html.find("<p", i)
        if pstart == -1:
            out.append(html[i:])
            break
        out.append(html[i:pstart])
        pend = html.find("</p>", pstart)
        if pend == -1:
            out.append(html[pstart:])
            break
        pblock = html[pstart:pend]
        span = f"<span id=\"clause-{idx}\">"
        # inject span after <p...>
        close = pblock.find(">")
        if close != -1:
            out.append(pblock[: close + 1] + span + pblock[close + 1 :] + "</span>")
        else:
            out.append(pblock)
        out.append("</p>")
        idx += 1
        i = pend + 4
    return "".join(out)


def parse_docx_bytes(file_bytes: bytes) -> Dict:
    """
    Robust DOCX parsing with graceful fallback. If mammoth fails (e.g., not a
    valid DOCX package), produce a plaintext-based single-page HTML.
    """
    buffer = BytesIO(file_bytes)
    html_spanned = ""
    text_plain = ""
    try:
        result = mammoth.convert_to_html(buffer)
        html = result.value or ""
        html_spanned = _wrap_spans(html)
        buffer.seek(0)
        text_plain = mammoth.extract_raw_text(buffer).value or ""
    except Exception:
        # Try python-docx for structured paragraphs
        try:
            from docx import Document  # type: ignore
            buffer.seek(0)
            doc = Document(buffer)
            paras = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
            if paras:
                parts: List[str] = ["<div class=\"page\">"]
                for i, p in enumerate(paras):
                    parts.append(f"<p><span id=\"clause-{i}\">{p}</span></p>")
                parts.append("</div>")
                html_spanned = "".join(parts)
                text_plain = "\n\n".join(paras)
            else:
                text_plain = ""
        except Exception:
            # Best-effort plaintext fallback
            try:
                text_plain = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text_plain = ""
            if text_plain:
                html_spanned = f"<div class=\"page\"><pre>{text_plain}</pre></div>"
            else:
                html_spanned = "<div class=\"page\"></div>"
    pages_json = {"pages": [{"index": 0, "html": html_spanned}]}
    return {"text_plain": text_plain, "pages_json": pages_json}


