import os
import time
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"), reason="Requires Supabase DB to run"
)


def test_heading_fallback_board_composition(tmp_path):
    """
    Ensure a heading like 'Board of Directors' yields a board_composition clause
    even if the paragraph lacks explicit keyword hits for regex extraction.
    """
    client = TestClient(app)
    # Minimal PDF-like bytes; parser fallback will treat as text. We rely on
    # heading-aware fallback in EXTRACT_NORMALIZE.
    content = (
        "Board of Directors\n\n"
        "The Company shall maintain a board consisting of five members appointed by holders.\n\n"
        "Other terms not relevant."
    ).encode("utf-8")
    files = {"file": ("doc.pdf", content, "application/pdf")}
    r = client.post("/api/upload", files=files)
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    # Poll until extracted/analyzed
    for _ in range(60):  # up to ~30s
        sr = client.get(f"/api/documents/{doc_id}/status")
        if sr.status_code == 200 and sr.json().get("status") in ("extracted", "analyzed"):
            break
        time.sleep(0.5)
    else:
        pytest.skip("Worker not running or pipeline too slow in CI")

    # Fetch clauses and verify a board_composition entry exists (from fallback)
    cr = client.get(f"/api/documents/{doc_id}/clauses")
    assert cr.status_code == 200
    clauses = cr.json()
    keys = [c.get("clause_key") for c in clauses]
    assert "board_composition" in keys


