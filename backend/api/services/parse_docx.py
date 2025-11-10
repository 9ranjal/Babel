from __future__ import annotations

from io import BytesIO
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import zipfile

try:  # pragma: no cover - optional dependency
    import mammoth  # type: ignore
except Exception:  # pragma: no cover
    mammoth = None

_HEADING_HINTS = {
    "company",
    "indian subsidiary",
    "founders",
    "investors",
    "existing investors",
    "investment amount",
    "valuation",
    "investors' ownership",
    "subscription right",
    "esop",
    "shareholding pattern",
    "use of proceeds",
    "closing conditions",
    "representations & warranties; indemnification",
    "investor directors",
    "protective provisions",
    "dividends",
    "liquidation preference",
    "conversion",
    "anti-dilution",
    "preemptive rights",
    "right of first refusal and co-sale",
    "drag-along",
    "exclusivity",
    "expenses",
    "confidentiality",
    "governing law and dispute resolution",
    "counterparts",
    "termination",
}


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


def _looks_like_heading(text: str) -> bool:
    raw = text.strip()
    if not raw:
        return False
    normalized = raw.replace("：", ":").strip()
    normalized_lower = " ".join(normalized.rstrip(":").split()).lower()
    if normalized_lower in _HEADING_HINTS:
        return True
    if normalized.endswith(":"):
        return True
    if any(c.isalpha() for c in raw) and raw == raw.upper() and len(normalized_lower.split()) <= 6:
        return True
    return False


def _generate_blocks(paragraphs: List[str]) -> List[Dict[str, object]]:
    blocks: List[Dict[str, object]] = []
    for idx, para in enumerate(paragraphs):
        text = para.strip()
        if not text:
            continue
        blocks.append(
            {
                "id": f"para-{idx}",
                "type": "heading" if _looks_like_heading(text) else "paragraph",
                "page": 0,
                "text": text,
            }
        )
    return blocks


DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _extract_docx_paragraphs_zip(file_bytes: bytes) -> List[str]:
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
            xml_bytes = zf.read("word/document.xml")
    except Exception:
        return []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    paragraphs: List[str] = []
    for p in root.findall(".//w:p", DOCX_NS):
        texts = []
        for t in p.findall(".//w:t", DOCX_NS):
            if t.text:
                texts.append(t.text)
        joined = "".join(texts).strip()
        if joined:
            paragraphs.append(joined)
    return paragraphs


def parse_docx_bytes(file_bytes: bytes) -> Dict:
    """
    Robust DOCX parsing with graceful fallback. If mammoth fails (e.g., not a
    valid DOCX package), produce a plaintext-based single-page HTML.
    """
    buffer = BytesIO(file_bytes)
    html_spanned = ""
    text_plain = ""
    paragraphs: List[str] = []
    mammoth_error: Optional[Exception] = None
    if mammoth is not None:
        try:
            result = mammoth.convert_to_html(buffer)
            html = result.value or ""
            html_spanned = _wrap_spans(html)
            buffer.seek(0)
            text_plain = mammoth.extract_raw_text(buffer).value or ""
            paragraphs = [p.strip() for p in text_plain.split("\n\n") if p.strip()]
        except Exception as exc:  # pragma: no cover - defensive
            mammoth_error = exc
    else:  # pragma: no cover - mammoth not installed
        mammoth_error = RuntimeError("mammoth unavailable")

    if not html_spanned and not text_plain:
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
                paragraphs = paras[:]
            else:
                text_plain = ""
        except Exception:
            paragraphs = _extract_docx_paragraphs_zip(file_bytes)
            if paragraphs:
                parts: List[str] = ["<div class=\"page\">"]
                for i, para in enumerate(paragraphs):
                    parts.append(f"<p><span id=\"clause-{i}\">{para}</span></p>")
                parts.append("</div>")
                html_spanned = "".join(parts)
                text_plain = "\n\n".join(paragraphs)
            else:
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
    if not paragraphs and text_plain:
        paragraphs = [p.strip() for p in text_plain.split("\n\n") if p.strip()]
    pages_json["blocks"] = _generate_blocks(paragraphs)
    return {"text_plain": text_plain, "pages_json": pages_json}


