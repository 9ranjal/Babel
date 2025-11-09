from __future__ import annotations

from typing import Iterable, List, Sequence


def embed_texts(texts: Sequence[str]) -> List[list[float]]:
    """
    Return deterministic embeddings for texts. In MVP/dev, this can be a stub or
    a call to a fixed model with temperature-equivalent deterministic behavior.
    """
    # Placeholder: zero-vectors; replace with real embeddings provider
    dim = 1536
    return [[0.0] * dim for _ in texts]


def batch_update_chunk_embeddings(
    chunk_ids: Iterable[str],
    embeddings: Iterable[list[float]],
) -> None:
    """
    Persist embeddings to the chunks table for provided chunk_ids.
    Left as a stub for MVP wiring; actual DB writes implemented in handlers.
    """
    return None


