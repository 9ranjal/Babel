from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


DEFAULT_LEVERAGE = {"investor": 0.6, "founder": 0.4}


def composite_score(b: Dict[str, Any], lev: Dict[str, float]) -> float:
    return (b.get("investor_score", 0) * lev["investor"]) + (b.get("founder_score", 0) * lev["founder"])


def pick_band(bands: List[Dict[str, Any]], attrs: Dict[str, Any], lev: Dict[str, float]) -> Optional[Dict[str, Any]]:
    v = (attrs or {}).get("value", None)

    def _match(b):
        if "range" in b and isinstance(v, (int, float)):
            lo, hi = b["range"]
            return lo <= v <= hi
        if "enum_match" in b and isinstance(v, str):
            return v == b["enum_match"]
        if "range" not in b and "enum_match" not in b:
            return True  # predicate-only, allow; business logic can refine
        return False

    matches = [b for b in bands if _match(b)]

    if not matches:
        return None

    matches.sort(key=lambda x: composite_score(x, lev), reverse=True)

    for m in matches:
        if m.get("name", "").lower() == "market":
            return m

    return matches[0]


def load_bands(repo_root: Optional[str] = None) -> Dict[str, Any]:
    root = repo_root or os.getcwd()
    path = os.path.join(root, "packages", "batna", "seed", "bands.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {"version": 1, "clauses": []}


def find_clause_band_spec(bands_data: Dict[str, Any], clause_key: str) -> Optional[Dict[str, Any]]:
    for c in bands_data.get("clauses", []):
        if c.get("clause_key") == clause_key:
            return c
    return None


