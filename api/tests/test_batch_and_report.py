from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_batch_lookup_resolves_and_reports_unresolved():
    session = MagicMock()

    def run_side_effect(query, **kwargs):
        q = kwargs.get("q")
        if q == "BRCA1":
            return MagicMock(
                single=lambda: {
                    "id": "ENSG00000012048",
                    "symbol": "BRCA1",
                    "name": "BRCA1 DNA repair",
                    "disease_count": 4,
                }
            )
        return MagicMock(single=lambda: None)

    session.run.side_effect = run_side_effect
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.post("/api/v1/genes/batch-lookup", json={"queries": ["BRCA1", "NOPE"]})

    assert r.status_code == 200
    body = r.json()
    assert body["hits"][0]["symbol"] == "BRCA1"
    assert body["hits"][0]["disease_count"] == 4
    assert body["unresolved"] == ["NOPE"]


def test_batch_lookup_requires_queries():
    r = client.post("/api/v1/genes/batch-lookup", json={"queries": []})
    assert r.status_code == 422


def test_gene_report_json_has_provenance_columns():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "ENSG00000012048", "symbol": "BRCA1"}),
        [
            {
                "disease_id": "MONDO_0007254",
                "disease_name": "breast cancer",
                "score": 0.92,
                "source": "opentargets",
                "evidence_json": '[{"evidence_type":"genetic_association","source":"gwas_catalog","score":0.45}]',
            }
        ],
    ]
    with patch("app.routers.export.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/export/gene-report?gene_id=ENSG00000012048")

    assert r.status_code == 200
    body = r.json()
    assert body["provenance"]["data_version"]
    assert body["associations"][0]["disease_name"] == "breast cancer"
    assert body["associations"][0]["evidence_types"] == "genetic_association"


def test_gene_report_tsv_download():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "ENSG00000012048", "symbol": "BRCA1"}),
        [
            {
                "disease_id": "MONDO_0007254",
                "disease_name": "breast cancer",
                "score": 0.92,
                "source": "opentargets",
                "evidence_json": "[]",
            }
        ],
    ]
    with patch("app.routers.export.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/export/gene-report?gene_id=ENSG00000012048&format=tsv")

    assert r.status_code == 200
    assert "text/tab-separated-values" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    lines = r.text.strip().splitlines()
    assert lines[0].split("\t")[0] == "gene_id"
    assert "breast cancer" in lines[1]
