from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


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


def pick_band(bands: list[Dict[str, Any]], attrs: Dict[str, Any], lev: Dict[str, float]):
    candidates: list[tuple[float, Dict[str, Any]]] = []
    for b in bands:
        investor = b.get("investor_score", 0.0)
        founder = b.get("founder_score", 0.0)
        score = investor * lev.get("investor", 0.5) + founder * lev.get("founder", 0.5)
        ok = True
        rng = b.get("range")
        if rng is not None and "value" in attrs:
            v = attrs["value"]
            ok = rng[0] <= v <= rng[1]
        if ok:
            candidates.append((score, b))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


