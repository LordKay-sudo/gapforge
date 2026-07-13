from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_meta_returns_provenance_without_neo4j():
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "bioinsight-graph"
    assert body["data_version"] == "opentargets-24.06-frozen-slice-v2"
    assert body["associations_are_correlative"] is True
    assert len(body["sources"]) >= 1
    assert "clinical" in body["disclaimer"].lower() or "not for" in body["disclaimer"].lower()
    assert body["web_ui_gene_path"] == "/gene/{gene_id}"
