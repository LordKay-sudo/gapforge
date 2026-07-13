from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.resolve_service import (
    Candidate,
    build_gene_resolution,
    pick_best,
    resolved_gene_id,
)

client = TestClient(app)


def test_pick_best_prefers_exact_symbol():
    candidates = [
        Candidate("ENSG1", "BRCA1"),
        Candidate("ENSG2", "BRCA1P1"),
    ]
    assert pick_best("BRCA1", candidates).id == "ENSG1"


def test_resolved_gene_id_format():
    body = resolved_gene_id("ENSG00000012048")
    assert body["canonical_id"] == "ENSG00000012048"
    assert body["id_system"] == "ENSG"


def test_build_gene_resolution_marks_ambiguity():
    candidates = [
        Candidate("ENSG1", "BRCA1"),
        Candidate("ENSG2", "BRCA1P1"),
    ]
    body = build_gene_resolution("brca", candidates)
    assert body["ambiguous"] is True
    assert len(body["candidates"]) == 1


def test_resolve_gene_endpoint():
    session = MagicMock()
    session.run.return_value = [
        {"id": "ENSG00000012048", "symbol": "BRCA1", "name": "BRCA1 DNA repair"}
    ]
    with patch("app.routers.resolve.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/resolve", params={"query": "BRCA1", "entity_type": "gene"})

    assert r.status_code == 200
    body = r.json()
    assert body["canonical_id"] == "ENSG00000012048"
    assert body["symbol"] == "BRCA1"
    assert body["ambiguous"] is False


def test_resolve_disease_not_found():
    session = MagicMock()
    session.run.return_value = []
    with patch("app.routers.resolve.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/resolve", params={"query": "NOPE", "entity_type": "disease"})

    assert r.status_code == 404
    assert r.json()["error"] is True


def test_resolve_gene_accepts_ensembl_id():
    session = MagicMock()
    session.run.return_value = MagicMock(single=lambda: {"symbol": "BRCA1"})
    with patch("app.routers.resolve.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get(
            "/api/v1/resolve",
            params={"query": "ENSG00000012048", "entity_type": "gene"},
        )

    assert r.status_code == 200
    assert r.json()["canonical_id"] == "ENSG00000012048"
