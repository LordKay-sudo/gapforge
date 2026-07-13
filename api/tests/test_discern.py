"""Tests for universal Discern layer."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.discern import POLICY_VERSION, discern
from app.gapforge import COU
from app.main import app

client = TestClient(app)


def test_discern_policy_endpoint():
    r = client.get("/api/v1/discern/policy?risk_tier=L2")
    assert r.status_code == 200
    body = r.json()
    assert body["policy_version"] == POLICY_VERSION
    assert "reliability" in body["thresholds"]


def test_discern_blocks_dosing_language():
    r = client.post(
        "/api/v1/discern",
        json={
            "artifact_type": "gap_hypothesis",
            "risk_tier": "L2",
            "cou": COU,
            "output": {
                "claim": "Patients should take 50 mg twice daily for Alzheimer disease.",
                "confidence": 0.9,
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["overall"] == "hard_fail"
    assert body["action"] == "block"
    assert body["scores"]["safety_language"]["passed"] is False


def test_discern_l3_always_blocked():
    raw = discern(
        artifact_type="generic",
        risk_tier="L3",
        cou=COU,
        output_payload={"claim": "Harmless exploratory note"},
    )
    assert raw["action"] == "block"
    assert raw["overall"] == "hard_fail"


def test_discern_l2_requires_hitl_even_when_passing():
    raw = discern(
        artifact_type="gap_hypothesis",
        risk_tier="L2",
        cou=COU,
        output_payload={
            "claim": "Endpoint sensitivity may have been insufficient in the mild AD cohort.",
            "confidence": 0.55,
            "insufficient_evidence": False,
            "supported_by_trial_ids": ["trial-flurizan-p3"],
            "literature_refs": [
                {"title": "PMC Flurizan lessons", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5350742/"}
            ],
            "provenance_hash": "abc123",
            "program_id": "prog-flurizan-ad",
            "data_version": "demo",
        },
    )
    assert raw["action"] == "require_hitl"
    assert raw["overall"] in ("pass", "soft_fail")
    assert raw["scores"]["compliance"]["passed"] is True
    assert raw["scores"]["safety_language"]["passed"] is True


def test_discern_weak_evidence_soft_fail():
    raw = discern(
        artifact_type="rag_answer",
        risk_tier="L1",
        cou=COU,
        output_payload={"answer": "Something about a target.", "confidence": 0.95},
    )
    assert raw["action"] in ("allow", "require_hitl")
    # High confidence + no evidence should soft-fail reliability
    assert raw["scores"]["reliability"]["passed"] is False or raw["overall"] == "soft_fail"
