from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import bindparam

from .band_map import load_bands, find_clause_band_spec, pick_band, composite_score
from .extract_regex import extract_attributes


async def analyze_clause(
    session: AsyncSession,
    document_id: str,
    clause_id: str,
    clause_key: Optional[str],
    clause_text: str,
    leverage: Dict[str, float] | None,
    attributes: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    bands_data = load_bands()
    spec = find_clause_band_spec(bands_data, clause_key or "") if clause_key else None
    # Derive attributes deterministically from stored clause text
    derived_attrs = extract_attributes(clause_text or "")
    band = None
    if spec:
        band = pick_band(
            spec.get("bands", []),
            derived_attrs or {},
            leverage or {"investor": 0.6, "founder": 0.4},
        )

    band_name = band.get("name") if band else None
    band_score = composite_score(band, leverage or {"investor": 0.6, "founder": 0.4}) if band else None

    # Determine posture based on band scores
    posture = "market"  # default
    if band:
        founder_score = band.get("founder_score", 0)
        investor_score = band.get("investor_score", 0)
        if founder_score > investor_score + 0.2:
            posture = "founder_friendly"
        elif investor_score > founder_score + 0.2:
            posture = "investor_friendly"
        else:
            posture = "market"

    analysis_json = {
        "posture": posture,
        "band_name": band_name,
        "band_score": band_score,
        "rationale": [band.get("rationale", "")] if band else [],
        "recommendation": f"Review {clause_key or 'clause'}; band={band_name or 'unknown'}",
        "trades": spec.get("trades", []) if spec else [],
    }

    inputs_json = {
        "clause_key": clause_key,
        "attributes": derived_attrs or {},
        "leverage": leverage or {"investor": 0.6, "founder": 0.4},
        "band_hint": band,
    }

    q = (
        text(
        """
        insert into public.analyses (id, document_id, clause_id, band_name, band_score, inputs_json, analysis_json, redraft_text)
            values (gen_random_uuid(), :document_id, :clause_id, :band_name, :band_score, :inputs_json, :analysis_json, null)
        on conflict (document_id, clause_id)
        do update set
          band_name = excluded.band_name,
          band_score = excluded.band_score,
          inputs_json = excluded.inputs_json,
          analysis_json = excluded.analysis_json
        returning id, clause_id, band_name, band_score, analysis_json, redraft_text
        """
        )
        .bindparams(bindparam("inputs_json", type_=JSONB))
        .bindparams(bindparam("analysis_json", type_=JSONB))
    )
    row = (
        await session.execute(
            q,
            {
                "document_id": document_id,
                "clause_id": clause_id,
                "band_name": band_name,
                "band_score": band_score,
                "inputs_json": inputs_json,
                "analysis_json": analysis_json,
            },
        )
    ).fetchone()

    return {
        "id": str(row.id),
        "clause_id": str(row.clause_id),
        "posture": row.analysis_json.get("posture") if row.analysis_json else None,
        "band_name": row.band_name,
        "band_score": float(row.band_score) if row.band_score is not None else None,
        "analysis_json": row.analysis_json,
        "trades": row.analysis_json.get("trades", []) if row.analysis_json else [],
        "redraft_text": row.redraft_text,
    }


