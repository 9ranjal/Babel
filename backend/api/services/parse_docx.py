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
    buffer = BytesIO(file_bytes)
    result = mammoth.convert_to_html(buffer)
    html = result.value or ""
    html_spanned = _wrap_spans(html)
    pages_json = {"pages": [{"index": 0, "html": html_spanned}]}
    buffer.seek(0)
    text_plain = mammoth.extract_raw_text(buffer).value or ""
    return {"text_plain": text_plain, "pages_json": pages_json}


