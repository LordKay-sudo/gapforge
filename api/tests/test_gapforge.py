"""GapForge API tests (mocked Neo4j session)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.gapforge import COU, VALID_GAP_CLASSES


client = TestClient(app)


def test_meta_includes_gapforge_disclaimer():
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    body = r.json()
    assert "GapForge" in body["disclaimer"] or "gap" in body["disclaimer"].lower()
    assert body["api_version"] == "0.3.1"


def test_gap_taxonomy_codes():
    assert "endpoint" in VALID_GAP_CLASSES
    assert "biomarker" in VALID_GAP_CLASSES
    assert len(VALID_GAP_CLASSES) >= 7


def _mock_session_for_list_programs():
    session = MagicMock()

    class FakeNode(dict):
        pass

    p = FakeNode(
        id="prog-flurizan-ad",
        name="Flurizan AD program",
        status="discontinued",
        indication_name="Alzheimer disease",
        moa="GSM",
        stall_summary="Phase 3 miss",
    )
    d = FakeNode(id="drug-tarenflurbil", name="tarenflurbil")

    result = MagicMock()
    result.__iter__ = lambda self: iter(
        [
            {
                "p": p,
                "d": d,
                "trial_count": 1,
                "gap_count": 3,
            }
        ]
    )
    session.run.return_value = result
    return session


@patch("app.routers.programs.get_session")
def test_list_programs(mock_get_session):
    session = _mock_session_for_list_programs()
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False
    r = client.get("/api/v1/programs")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["id"] == "prog-flurizan-ad"
    assert data[0]["gap_count"] == 3


@patch("app.routers.reviews.get_session")
def test_review_decision_validation(mock_get_session):
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "g": {"id": "gap-x", "discern_json": None},
    }
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False
    r = client.post(
        "/api/v1/reviews/gap-x",
        json={"decision": "approve", "reviewer": "tester", "notes": "ok"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved"
    assert body["cou"] == COU


@patch("app.routers.reviews.get_session")
def test_review_approve_blocked_by_discern(mock_get_session):
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "g": {
            "id": "gap-x",
            "discern_json": '{"action": "block", "overall": "hard_fail"}',
        },
    }
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False
    r = client.post(
        "/api/v1/reviews/gap-x",
        json={"decision": "approve", "reviewer": "tester", "notes": "ok"},
    )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "block" in detail["message"].lower()


@patch("app.routers.gaps.get_session")
def test_run_gap_discern_persists(mock_get_session):
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "g": {
            "id": "gap-x",
            "claim": "Endpoint sensitivity may have been insufficient in the mild AD cohort.",
            "confidence": 0.55,
            "gap_class": "endpoint",
            "risk_tier": "L2",
            "cou": COU,
            "insufficient_evidence": False,
            "provenance_hash": "abc123",
            "literature_refs_json": '[{"title": "PMC", "url": "https://pmc.ncbi.nlm.nih.gov/"}]',
            "suggested_experiment": "Re-analyse endpoint sensitivity",
            "critic_notes": None,
        },
        "program_id": "prog-flurizan-ad",
    }
    mock_get_session.return_value.__enter__.return_value = session
    mock_get_session.return_value.__exit__.return_value = False
    r = client.post("/api/v1/gaps/gap-x/discern")
    assert r.status_code == 200
    body = r.json()
    assert body["action"] in ("allow", "require_hitl", "block")
    assert body["risk_tier"] == "L2"
    # Second session.run persists discern_json
    assert session.run.call_count >= 2
    persist_kwargs = session.run.call_args_list[-1].kwargs
    assert "discern_json" in persist_kwargs
    assert '"action"' in persist_kwargs["discern_json"]


def test_review_invalid_decision():
    r = client.post("/api/v1/reviews/gap-x", json={"decision": "maybe"})
    assert r.status_code == 400
