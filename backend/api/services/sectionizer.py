from typing import Any, Dict, List

from .numbering import strip_leading_numbering


def sectionize(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None

    for block in blocks or []:
        btype = (block.get("type") or "").lower()
        text = (block.get("text") or "").strip()
        page = block.get("page")
        block_id = block.get("id")

        if btype == "heading" and text:
            title, _ = strip_leading_numbering(text)
            if current:
                sections.append(current)
            current = {
                "title": title.strip(),
                "page_start": page,
                "page_end": page,
                "block_ids": [block_id],
                "body": [],
            }
        else:
            if current is None:
                current = {
                    "title": "",
                    "page_start": page,
                    "page_end": page,
                    "block_ids": [],
                    "body": [],
                }
            current["page_end"] = page
            if block_id is not None:
                current["block_ids"].append(block_id)
            if text:
                current["body"].append(text)

    if current:
        sections.append(current)

    for section in sections:
        section["text"] = "\n".join([t for t in section.pop("body", []) if t])

    return sections


