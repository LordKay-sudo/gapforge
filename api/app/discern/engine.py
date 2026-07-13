"""Discern engine: run checkers, apply thresholds, emit overall action."""
from __future__ import annotations

from typing import Any

from app.discern.checkers import (
    check_compliance,
    check_provenance,
    check_reliability,
    check_safety_language,
)
from app.discern.policy import ALL_DIMENSIONS, POLICY_VERSION, merge_thresholds
from app.gapforge import provenance_hash


def discern(
    *,
    artifact_type: str,
    risk_tier: str,
    cou: str | None = None,
    input_payload: dict[str, Any] | None = None,
    output_payload: dict[str, Any] | None = None,
    dimensions: list[str] | None = None,
    threshold_overrides: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Weigh input/output against policy thresholds.

    overall: pass | soft_fail | hard_fail
    action:  allow | require_hitl | block
    """
    tier = (risk_tier or "L2").upper()
    if tier not in ("L0", "L1", "L2", "L3"):
        tier = "L2"

    dims = [d for d in (dimensions or list(ALL_DIMENSIONS)) if d in ALL_DIMENSIONS]
    if not dims:
        dims = list(ALL_DIMENSIONS)

    thresholds = merge_thresholds(tier, threshold_overrides)
    scores: dict[str, dict[str, Any]] = {}
    all_reasons: list[dict[str, Any]] = []

    runners = {
        "compliance": lambda: check_compliance(
            risk_tier=tier,
            cou=cou,
            input_payload=input_payload,
            output_payload=output_payload,
        ),
        "safety_language": lambda: check_safety_language(
            risk_tier=tier,
            input_payload=input_payload,
            output_payload=output_payload,
        ),
        "reliability": lambda: check_reliability(risk_tier=tier, output_payload=output_payload),
        "provenance": lambda: check_provenance(
            risk_tier=tier,
            input_payload=input_payload,
            output_payload=output_payload,
        ),
    }

    hard = False
    soft = False

    for dim in dims:
        score, reasons = runners[dim]()
        thr = float(thresholds.get(dim, 0.5))
        passed = score >= thr
        # Any hard severity reason fails the dimension hard
        dim_hard = any(r.get("severity") == "hard" for r in reasons)
        if dim_hard:
            passed = False
            hard = True
        elif not passed:
            soft = True

        scores[dim] = {
            "score": round(score, 3),
            "threshold": thr,
            "passed": passed,
        }
        all_reasons.extend(reasons)

    if tier == "L3":
        hard = True

    if hard:
        overall = "hard_fail"
        action = "block"
    elif soft or tier == "L2":
        # L2 always require_hitl even on full pass (never auto-approve team conclusions)
        overall = "soft_fail" if soft else "pass"
        action = "require_hitl"
    else:
        overall = "pass"
        action = "allow"

    phash = provenance_hash(
        POLICY_VERSION,
        artifact_type,
        tier,
        str(scores),
        cou or "",
    )

    return {
        "overall": overall,
        "action": action,
        "scores": scores,
        "reasons": all_reasons,
        "policy_version": POLICY_VERSION,
        "risk_tier": tier,
        "artifact_type": artifact_type,
        "cou": cou,
        "provenance_hash": phash,
        "note": (
            "Discern never auto-approves L2 team conclusions; "
            "require_hitl means human review remains mandatory."
            if action == "require_hitl"
            else None
        ),
    }
