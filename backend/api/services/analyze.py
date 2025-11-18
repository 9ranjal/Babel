from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import bindparam

from .extract_regex import extract_attributes
from .banding import band_clause, canonical
from .band_map import composite_score, DEFAULT_LEVERAGE


async def analyze_clause(
    session: AsyncSession,
    document_id: str,
    clause_id: str,
    clause_key: Optional[str],
    clause_text: str,
    leverage: Dict[str, float] | None,
    attributes: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    # Derive attributes deterministically from stored clause text
    derived_attrs = extract_attributes(clause_text or "")
    # Compute banding using shared utility (handles aliases + badges)
    info = band_clause(canonical(clause_key or ""), derived_attrs, leverage or DEFAULT_LEVERAGE)
    band = info.get("band")
    band_name = info.get("band_name")
    band_score = composite_score(band, leverage or DEFAULT_LEVERAGE) if band else None

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
        "rationale": info.get("rationale", []),
        "recommendation": f"Review {clause_key or 'clause'}; band={band_name or 'unknown'}",
        "trades": info.get("trades", []),
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


