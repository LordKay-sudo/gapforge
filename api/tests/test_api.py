from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    with patch("app.routers.health.check_connectivity", return_value=True):
        r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["neo4j"] is True


def test_search_genes():
    session = MagicMock()
    session.run.return_value = [
        {"id": "ENSG1", "symbol": "BRCA1", "name": "BRCA1 DNA repair associated"}
    ]
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes?q=BRCA")
    assert r.status_code == 200
    assert r.json()[0]["symbol"] == "BRCA1"


def test_neighbors_shape():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"g": True}),
        [
            {"label": "Gene", "id": "ENSG1", "name": "BRCA1", "symbol": "BRCA1"},
            {"label": "Disease", "id": "MONDO_1", "name": "breast cancer", "symbol": None},
        ],
        [
            {"source": "ENSG1", "target": "MONDO_1", "type": "ASSOCIATED_WITH", "score": 0.9},
        ],
    ]
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes/ENSG1/neighbors")
    assert r.status_code == 200
    body = r.json()
    assert body["gene_id"] == "ENSG1"
    assert "nodes" in body
    assert "edges" in body
