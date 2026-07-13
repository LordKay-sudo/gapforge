"""Universal Discern API — weigh I/O against compliance/reliability thresholds."""
from __future__ import annotations

from fastapi import APIRouter

from app.discern import discern
from app.discern.policy import POLICY_VERSION, policy_snapshot
from app.gapforge import COU
from app.models.schemas import (
    DimensionScore,
    DiscernReason,
    DiscernRequest,
    DiscernResponse,
)

router = APIRouter(prefix="/discern", tags=["discern"])


def to_response(raw: dict) -> DiscernResponse:
    scores = {
        k: DimensionScore(**v) if isinstance(v, dict) else v
        for k, v in (raw.get("scores") or {}).items()
    }
    reasons = [DiscernReason(**r) if isinstance(r, dict) else r for r in raw.get("reasons") or []]
    return DiscernResponse(
        overall=raw["overall"],
        action=raw["action"],
        scores=scores,
        reasons=reasons,
        policy_version=raw["policy_version"],
        risk_tier=raw["risk_tier"],
        artifact_type=raw["artifact_type"],
        cou=raw.get("cou"),
        provenance_hash=raw["provenance_hash"],
        note=raw.get("note"),
    )


@router.get("/policy")
def get_policy(risk_tier: str = "L2") -> dict:
    """Return active discern policy version and thresholds for a risk tier."""
    return policy_snapshot(risk_tier)


@router.post("", response_model=DiscernResponse)
def post_discern(body: DiscernRequest) -> DiscernResponse:
    """
    Weigh input/output against policy thresholds.

    overall: pass | soft_fail | hard_fail
    action: allow | require_hitl | block

    Never auto-approves L2 team conclusions (L2 always require_hitl on non-block).
    """
    raw = discern(
        artifact_type=body.artifact_type,
        risk_tier=body.risk_tier,
        cou=body.cou or COU,
        input_payload=body.input,
        output_payload=body.output,
        dimensions=body.dimensions,
        threshold_overrides=body.thresholds,
    )
    return to_response(raw)


@router.get("/version")
def discern_version() -> dict:
    return {"policy_version": POLICY_VERSION}
