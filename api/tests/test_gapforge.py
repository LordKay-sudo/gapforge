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
    session.run.return_value.single.return_value = {"id": "gap-x"}
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


def test_review_invalid_decision():
    r = client.post("/api/v1/reviews/gap-x", json={"decision": "maybe"})
    assert r.status_code == 400
