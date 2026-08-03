"""Tests for OntoHarness L2 gates in GapForge."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.gapforge import COU


client = TestClient(app)


@patch("app.routers.reviews.validate_gap_hypothesis")
@patch("app.routers.reviews.get_session")
def test_review_approve_blocked_by_ontoharness(mock_get_session, mock_validate):
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "g": {"id": "gap-x", "discern_json": None, "claim": "test", "confidence": 0.5},
        "genes": [],
        "disease": None,
    }
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False
    mock_validate.return_value = {
        "conforms": False,
        "vocab_violations": [{"term": "bio:fake", "term_kind": "property", "message": "bad"}],
        "repair_hints": ["fix it"],
    }

    r = client.post(
        "/api/v1/reviews/gap-x",
        json={"decision": "approve", "reviewer": "tester", "notes": "ok"},
    )
    assert r.status_code == 422
    assert "OntoHarness" in r.json()["detail"]["message"]


@patch("app.routers.gaps.validate_gap_hypothesis")
@patch("app.routers.gaps.get_session")
def test_run_gap_ontology_validate_persists(mock_get_session, mock_validate):
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "g": {
            "id": "gap-x",
            "claim": "Endpoint sensitivity may have been insufficient.",
            "confidence": 0.55,
        },
        "genes": [{"id": "ENSG1", "symbol": "BRCA1"}],
        "disease": {"id": "MONDO_1", "name": "Alzheimer disease"},
    }
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False
    mock_validate.return_value = {
        "domain": "biomedical",
        "conforms": True,
        "vocab_violations": [],
        "shacl_violations": [],
        "repair_hints": [],
    }

    r = client.post("/api/v1/gaps/gap-x/ontology-validate")
    assert r.status_code == 200
    body = r.json()
    assert body["conforms"] is True
    persist_kwargs = session.run.call_args_list[-1].kwargs
    assert "ontology_validation_json" in persist_kwargs


def test_gap_hypothesis_rdf_includes_label():
    from app.ontology_rdf import gap_hypothesis_to_turtle

    turtle = gap_hypothesis_to_turtle("gap-1", "Endpoint gap", 0.6, [], None)
    assert "bio:Hypothesis" in turtle
    assert "Endpoint gap" in turtle
