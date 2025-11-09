import os
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"), reason="Requires Supabase DB to run"
)


def test_upload_checksum_short_circuit(monkeypatch, tmp_path):
    client = TestClient(app)
    data = b"hello world" * 100
    fpath = tmp_path / "doc.pdf"
    fpath.write_bytes(data)

    files = {"file": ("doc.pdf", data, "application/pdf")}
    r1 = client.post("/api/upload", files=files)
    assert r1.status_code == 200
    doc_id_1 = r1.json()["document_id"]

    r2 = client.post("/api/upload", files=files)
    assert r2.status_code == 200
    doc_id_2 = r2.json()["document_id"]

    assert doc_id_1 == doc_id_2


