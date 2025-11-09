from __future__ import annotations

from typing import Any, Dict, List


def _coerce_attrs(attrs: Any) -> Dict[str, Any]:
    if isinstance(attrs, dict):
        return attrs
    return {}


def normalize_snippets(snippets: List[Dict], temperature: float = 0.0) -> List[Dict]:
    # Deterministic normalization; `temperature` placeholder keeps API stable.
    del temperature  # unused but retained for interface compatibility

    normalized: List[Dict] = []
    for snippet in snippets:
        attrs = _coerce_attrs(snippet.get("attributes"))
        block_ids = [str(b) for b in (snippet.get("block_ids") or []) if b is not None]
        meta: Dict[str, Any] = {
            "block_ids": block_ids,
            "source": snippet.get("source", "regex"),
        }
        if attrs:
            meta["attributes"] = attrs
        if snippet.get("title"):
            meta["title"] = snippet.get("title")

        normalized.append(
            {
                "clause_key": snippet.get("clause_key"),
                "title": snippet.get("title"),
                "text": snippet.get("text"),
                "start_idx": snippet.get("start_idx"),
                "end_idx": snippet.get("end_idx"),
                "page_hint": snippet.get("page_hint"),
                "attributes": attrs,
                "block_ids": block_ids,
                "confidence": float(snippet.get("confidence", 0.7)),
                "json_meta": meta,
            }
        )

    return normalized


