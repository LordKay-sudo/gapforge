from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_disease():
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "id": "MONDO_1",
        "name": "breast cancer",
        "gene_count": 3,
    }
    with patch("app.routers.diseases.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/diseases/MONDO_1")
    assert r.status_code == 200
    assert r.json()["gene_count"] == 3


def test_get_disease_genes_ranked():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "MONDO_1", "name": "breast cancer"}),
        [
            {
                "gene_id": "ENSG1",
                "symbol": "BRCA1",
                "name": "BRCA1",
                "score": 0.92,
                "source": "opentargets",
                "evidence_json": "[]",
            },
            {
                "gene_id": "ENSG2",
                "symbol": "TP53",
                "name": "TP53",
                "score": 0.71,
                "source": "opentargets",
                "evidence_json": "[]",
            },
        ],
    ]
    with patch("app.routers.diseases.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/diseases/MONDO_1/genes?min_score=0.5")
    assert r.status_code == 200
    body = r.json()
    assert body["genes"][0]["symbol"] == "BRCA1"
    assert body["genes"][0]["score"] == 0.92


def test_get_gene_diseases_ranked():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "ENSG1", "symbol": "BRCA1"}),
        [
            {
                "disease_id": "MONDO_1",
                "name": "breast cancer",
                "score": 0.9,
                "source": "opentargets",
                "evidence_json": "[]",
            }
        ],
    ]
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes/ENSG1/diseases")
    assert r.status_code == 200
    assert r.json()["diseases"][0]["name"] == "breast cancer"


def test_compare_genes():
    session = MagicMock()

    def run_side_effect(query, **kwargs):
        symbol = kwargs.get("symbol")
        if symbol == "BRCA1":
            return MagicMock(
                single=lambda: {"id": "ENSG1", "symbol": "BRCA1", "name": "BRCA1"},
                __iter__=lambda self: iter([]),
            )
        if symbol == "TP53":
            return MagicMock(
                single=lambda: {"id": "ENSG2", "symbol": "TP53", "name": "TP53"},
                __iter__=lambda self: iter([]),
            )
        if "disease_count" in query:
            return MagicMock(single=lambda: {"disease_count": 2})
        if "ORDER BY r.score" in query:
            mock = MagicMock()
            row = {
                "disease_id": "MONDO_1",
                "name": "breast cancer",
                "score": 0.9 if kwargs.get("id") == "ENSG1" else 0.8,
                "source": "opentargets",
                "evidence_json": "[]",
            }
            mock.__iter__ = lambda self: iter([row])
            return mock
        return MagicMock(single=lambda: None)

    session.run.side_effect = run_side_effect
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes/compare?symbols=BRCA1,TP53")
    assert r.status_code == 200
    body = r.json()
    assert len(body["genes"]) == 2
    assert "breast cancer" in body["overlapping_disease_names"]
