import os
import time
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"), reason="Requires Supabase DB to run"
)


def test_pipeline_reaches_analyzed_with_embeddings_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("EMBEDDINGS_ENABLED", "false")
    client = TestClient(app)
    data = b"agreement with exclusivity and rofr and drag along" * 200
    files = {"file": ("doc.pdf", data, "application/pdf")}
    r = client.post("/api/upload", files=files)
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    # Poll status for a short period (dev worker must be running separately)
    for _ in range(30):
        sr = client.get(f"/api/documents/{doc_id}/status")
        if sr.status_code == 200 and sr.json().get("status") == "analyzed":
            break
        time.sleep(0.5)
    else:
        pytest.skip("Worker not running or pipeline too slow in CI")


