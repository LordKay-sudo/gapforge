"""Tests for approved RDF export."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.ontology_rdf import merge_turtle_documents

client = TestClient(app)


def test_merge_turtle_documents_deduplicates_prefixes():
    a = "@prefix bio: <https://ontoharness.dev/biomedical#> .\nbio:a a bio:Hypothesis ."
    b = "@prefix bio: <https://ontoharness.dev/biomedical#> .\nbio:b a bio:Hypothesis ."
    merged = merge_turtle_documents([a, b])
    assert merged.count("@prefix bio:") == 1
    assert "bio:a" in merged
    assert "bio:b" in merged


@patch("app.routers.export.get_session")
def test_export_approved_rdf_by_gap_id(mock_get_session):
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "g": {
            "id": "gap-x",
            "claim": "Test claim",
            "confidence": 0.5,
            "gap_class": "efficacy",
            "status": "approved",
            "approved_rdf_turtle": "@prefix bio: <https://ontoharness.dev/biomedical#> .\nbio:gap-x a bio:Hypothesis .",
        },
        "genes": [],
        "disease": None,
    }
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False

    r = client.get("/api/v1/export/approved-rdf?gap_id=gap-x")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/turtle")
    assert "bio:Hypothesis" in r.text
