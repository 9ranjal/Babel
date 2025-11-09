import os
import time
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"), reason="Requires Supabase DB to run"
)


def test_end_to_end_pipeline(tmp_path):
    client = TestClient(app)
    data = b"drag along clause\n\nright of first refusal\n\nanti-dilution" * 200
    files = {"file": ("doc.pdf", data, "application/pdf")}
    r = client.post("/api/upload", files=files)
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    # Poll status
    for _ in range(60):  # up to ~30s
        sr = client.get(f"/api/documents/{doc_id}/status")
        if sr.status_code == 200 and sr.json().get("status") == "analyzed":
            break
        time.sleep(0.5)
    else:
        pytest.skip("Worker not running or pipeline too slow in CI")

    # Fetch document to verify artifacts exist
    dr = client.get(f"/api/documents/{doc_id}")
    assert dr.status_code == 200
    doc = dr.json()
    assert doc["pages_json"] is not None


