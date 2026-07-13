from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_subgraph():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"g": True}),
        [
            {"label": "Gene", "id": "ENSG1", "name": "BRCA1", "symbol": "BRCA1"},
            {"label": "Disease", "id": "MONDO_1", "name": "breast cancer", "symbol": None},
        ],
        [
            {"source": "ENSG1", "target": "MONDO_1", "type": "ASSOCIATED_WITH", "score": 0.91},
        ],
    ]
    with patch("app.routers.export.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/export/subgraph?gene_id=ENSG1")
    assert r.status_code == 200
    body = r.json()
    assert body["gene_id"] == "ENSG1"
    assert len(body["nodes"]) == 2
    assert len(body["links"]) == 1
    assert body["links"][0]["type"] == "ASSOCIATED_WITH"
