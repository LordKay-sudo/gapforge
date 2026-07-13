import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.evidence import parse_evidence_items
from app.main import app

client = TestClient(app)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "opentargets_slice_v2.json"


def test_parse_evidence_items_from_json_string():
    raw = json.dumps(
        [
            {"evidence_type": "genetic_association", "source": "gwas_catalog", "score": 0.42, "study_id": "GCST1"},
            {"evidence_type": "literature", "source": "europepmc", "score": 0.31},
        ]
    )
    items = parse_evidence_items(raw)
    assert len(items) == 2
    assert items[0].evidence_type == "genetic_association"
    assert items[0].study_id == "GCST1"


def test_frozen_fixture_meets_p0_scale():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    genes = {a["target_id"] for a in data["associations"]}
    assert len(genes) >= 500
    assert len(data["associations"]) >= 3000


def test_get_gene_diseases_includes_evidence():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "ENSG00000012048", "symbol": "BRCA1"}),
        [
            {
                "disease_id": "MONDO_0007254",
                "name": "breast cancer",
                "score": 0.92,
                "source": "opentargets",
                "evidence_json": json.dumps(
                    [{"evidence_type": "genetic_association", "source": "gwas_catalog", "score": 0.45}]
                ),
            }
        ],
    ]
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes/ENSG00000012048/diseases")
    assert r.status_code == 200
    body = r.json()
    assert body["diseases"][0]["source"] == "opentargets"
    assert body["diseases"][0]["evidence"][0]["evidence_type"] == "genetic_association"


def test_get_gene_evidence_endpoint():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "ENSG00000012048", "symbol": "BRCA1"}),
        [
            {
                "disease_id": "MONDO_0007254",
                "disease_name": "breast cancer",
                "score": 0.92,
                "source": "opentargets",
                "evidence_json": json.dumps(
                    [
                        {"evidence_type": "genetic_association", "source": "gwas_catalog", "score": 0.45},
                        {"evidence_type": "literature", "source": "europepmc", "score": 0.22},
                    ]
                ),
            }
        ],
    ]
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes/ENSG00000012048/evidence")
    assert r.status_code == 200
    body = r.json()
    assert body["gene_id"] == "ENSG00000012048"
    assert "evidence" in body
    assert len(body["evidence"][0]["evidence"]) == 2


def test_get_gene_evidence_filtered_by_disease_not_found():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(single=lambda: {"id": "ENSG00000012048", "symbol": "BRCA1"}),
        [],
    ]
    with patch("app.routers.genes.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/genes/ENSG00000012048/evidence?disease_id=MONDO_MISSING")
    assert r.status_code == 404


def test_etl_v2_fixture_produces_evidence_columns():
    import importlib.util

    etl_path = Path(__file__).resolve().parents[2] / "scripts" / "etl_opentargets.py"
    spec = importlib.util.spec_from_file_location("etl_opentargets", etl_path)
    etl = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(etl)

    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    associations, _ = etl.transform(data)
    assert "evidence_json" in associations.columns
    assert "evidence_type" in associations.columns
    assert associations["target_id"].nunique() >= 500
