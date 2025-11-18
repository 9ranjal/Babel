from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .band_map import (
    DEFAULT_LEVERAGE,
    load_bands,
    find_clause_band_spec,
    pick_band,
    composite_score,
)

# Shared alias map for banding lookups
ALIASES: Dict[str, str] = {
    "information_inspection_rights": "information_rights",
    "right_of_first_refusal": "rofr",
    "preemptive_rights": "preemptive_pro_rata",
    "exit_rights": "exit",
}


def canonical(key: str | None) -> str:
    raw = (key or "").strip()
    return ALIASES.get(raw, raw)


def _derive_value_for_band(key: str, attrs: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str]]:
    """
    Return (value, badge) to feed into pick_band for known keys.
    Badge is a compact display string for the UI (e.g., '60d', '5y', '12%').
    """
    k = canonical(key)
    a = attrs or {}

    if k == "exclusivity":
        v = a.get("exclusivity_days") or a.get("days")
        return (v, f"{int(v)}d" if isinstance(v, (int, float)) else None)

    if k in {"rofr", "rofo"}:
        v = a.get("days")
        return (v, f"{int(v)}d" if isinstance(v, (int, float)) else None)

    if k == "option_pool":
        v = a.get("pool_percent")
        return (v, f"{float(v):g}%" if isinstance(v, (int, float)) else None)

    if k == "exit":
        v = a.get("years")
        return (v, f"{int(v)}y" if isinstance(v, (int, float)) else None)

    if k == "anti_dilution":
        v = a.get("antidilution_type")
        return (v, str(v) if isinstance(v, str) else None)

    if k == "liquidation_preference":
        # Map multiple + participation to enum expected by bands.json
        multiple = a.get("liq_multiple")
        part = (a.get("participation") or "").strip().lower()
        if multiple in (1, 1.0) and part.startswith("non"):
            return ("1x_np", "1x_np")
        if multiple in (1, 1.0) and part.startswith("participating"):
            return ("1x_p", "1x_p")
        if isinstance(multiple, (int, float)) and multiple and multiple > 1:
            if part.startswith("participating"):
                return (">1x_p", ">1x_p")
            if part.startswith("non"):
                return (">1x_np", ">1x_np")
        return (None, None)

    if k == "reserved_matters":
        v = a.get("reserved_list")
        return (v, str(v) if v else None)

    if k == "information_rights":
        v = a.get("info_level")
        return (v, str(v) if v else None)

    if k == "board":
        v = a.get("board_structure")
        return (v, str(v) if v else None)

    if k == "pay_to_play":
        v = a.get("pay_to_play")
        return (v, str(v) if v else None)

    # Unknown/unsupported for banding
    return (None, None)


def band_clause(
    clause_key: str | None,
    attributes: Dict[str, Any] | None,
    leverage: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """
    Compute banding info for a clause:
    - band (dict or None)
    - band_name (str or None)
    - badge (compact display string) and tilt (founder_friendly | investor_friendly | market | unknown)
    - rationale, trades (from spec when available)
    """
    key = canonical(clause_key or "")
    bands_data = load_bands()
    spec = find_clause_band_spec(bands_data, key)
    if not spec:
        return {"band": None, "band_name": None, "badge": None, "tilt": "unknown", "rationale": [], "trades": []}

    v, badge = _derive_value_for_band(key, attributes or {})
    band = None
    if v is not None:
        band = pick_band(spec.get("bands", []), {"value": v}, leverage or DEFAULT_LEVERAGE)

    band_name = band.get("name") if band else None
    # Determine tilt
    tilt = "unknown"
    if band:
        f = band.get("founder_score", 0.0)
        i = band.get("investor_score", 0.0)
        if f > i + 0.2:
            tilt = "founder_friendly"
        elif i > f + 0.2:
            tilt = "investor_friendly"
        else:
            tilt = "market"

    return {
        "band": band,
        "band_name": band_name,
        "badge": badge,
        "tilt": tilt,
        "rationale": [band.get("rationale", "")] if band else [],
        "trades": spec.get("trades", []),
    }


