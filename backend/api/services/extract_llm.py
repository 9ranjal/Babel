from __future__ import annotations

from typing import Dict, List


def normalize_snippets(snippets: List[Dict]) -> List[Dict]:
    # Deterministic: pass-through for MVP, ensure required fields present
    out: List[Dict] = []
    for s in snippets:
        out.append(
            {
                "clause_key": s.get("clause_key"),
                "title": s.get("title"),
                "text": s.get("text"),
                "attributes": s.get("attributes", {}),
                "confidence": float(s.get("confidence", 0.7)),
                "start_idx": s.get("start_idx"),
                "end_idx": s.get("end_idx"),
                "page_hint": s.get("page_hint"),
            }
        )
    return out


