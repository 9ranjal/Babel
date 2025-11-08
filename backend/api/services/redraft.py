from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def save_redraft(session: AsyncSession, document_id: str, clause_id: str, original_text: str) -> dict[str, Any]:
    # Deterministic placeholder: wrap original suggesting edits
    redraft_text = f"Notwithstanding the foregoing, the parties agree: {original_text}"
    q = text(
        """
        update public.analyses
        set redraft_text = :redraft_text
        where document_id = :document_id and clause_id = :clause_id
        returning id, clause_id, band_name, band_score, analysis_json, redraft_text
        """
    )
    row = (
        await session.execute(
            q,
            {
                "document_id": document_id,
                "clause_id": clause_id,
                "redraft_text": redraft_text,
            },
        )
    ).fetchone()
    return {
        "id": str(row.id),
        "clause_id": str(row.clause_id),
        "band_name": row.band_name,
        "band_score": float(row.band_score) if row.band_score is not None else None,
        "analysis_json": row.analysis_json,
        "redraft_text": row.redraft_text,
    }


