"""Gap hypothesis propose / critic / list endpoints (L2 — HITL required)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.db import get_session
from app.discern import discern
from app.gapforge import (
    COU,
    VALID_GAP_CLASSES,
    parse_json_list,
    provenance_hash,
)
from app.models.schemas import (
    CriticRequest,
    CriticResponse,
    GapHypothesisDetail,
    GapHypothesisSummary,
    ProposeGapsRequest,
    ProposeGapsResponse,
)
from app.routers.discern import to_response


router = APIRouter(prefix="/gaps", tags=["gapforge-gaps"])


def _parse_discern(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else None
    except json.JSONDecodeError:
        return None


def _hyp_summary(node: dict, program_id: str | None = None) -> GapHypothesisSummary:
    return GapHypothesisSummary(
        id=node["id"],
        gap_class=node.get("gap_class") or "efficacy",
        claim=node.get("claim") or "",
        confidence=float(node.get("confidence") or 0),
        status=node.get("status") or "needs_review",
        risk_tier=node.get("risk_tier") or "L2",
        insufficient_evidence=bool(node.get("insufficient_evidence")),
        program_id=program_id,
        suggested_experiment=node.get("suggested_experiment"),
        provenance_hash=node.get("provenance_hash"),
        critic_notes=node.get("critic_notes"),
        literature_refs=parse_json_list(node.get("literature_refs_json")),
        discern=_parse_discern(node.get("discern_json")),
    )


@router.get("", response_model=list[GapHypothesisSummary])
def list_gaps(
    program_id: str | None = None,
    status: str | None = Query(None, description="draft|needs_review|approved|rejected"),
) -> list[GapHypothesisSummary]:
    with get_session() as session:
        if program_id:
            rows = session.run(
                """
                MATCH (g:GapHypothesis)-[:ABOUT]->(p:Program {id: $program_id})
                WHERE $status IS NULL OR g.status = $status
                RETURN g, p.id AS program_id
                ORDER BY g.confidence DESC
                """,
                program_id=program_id,
                status=status,
            )
        else:
            rows = session.run(
                """
                MATCH (g:GapHypothesis)
                OPTIONAL MATCH (g)-[:ABOUT]->(p:Program)
                WHERE $status IS NULL OR g.status = $status
                RETURN g, p.id AS program_id
                ORDER BY g.confidence DESC
                """,
                status=status,
            )
        return [_hyp_summary(dict(row["g"]), row["program_id"]) for row in rows]


@router.get("/{gap_id}", response_model=GapHypothesisDetail)
def get_gap(gap_id: str) -> GapHypothesisDetail:
    with get_session() as session:
        row = session.run(
            """
            MATCH (g:GapHypothesis {id: $id})
            OPTIONAL MATCH (g)-[:ABOUT]->(p:Program)
            OPTIONAL MATCH (g)-[:SUPPORTED_BY]->(s)
            OPTIONAL MATCH (g)-[:CONTRADICTED_BY]->(c)
            OPTIONAL MATCH (r:Review)-[:REVIEWS]->(g)
            RETURN g, p.id AS program_id, p.name AS program_name,
                   collect(DISTINCT {id: s.id, labels: labels(s)}) AS supported,
                   collect(DISTINCT {id: c.id, labels: labels(c)}) AS contradicted,
                   collect(DISTINCT r {
                     .id, .decision, .reviewer, .notes, .decided_at
                   }) AS reviews
            """,
            id=gap_id,
        ).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Gap hypothesis not found: {gap_id}")
        g = dict(row["g"])
        base = _hyp_summary(g, row["program_id"])
        return GapHypothesisDetail(
            **base.model_dump(),
            program_name=row["program_name"],
            cou=g.get("cou") or COU,
            critic_confidence=g.get("critic_confidence"),
            supported_by=[x for x in row["supported"] if x.get("id")],
            contradicted_by=[x for x in row["contradicted"] if x.get("id")],
            reviews=[r for r in row["reviews"] if r and r.get("id")],
        )


@router.post("/propose", response_model=ProposeGapsResponse)
def propose_gaps(body: ProposeGapsRequest) -> ProposeGapsResponse:
    """Create L2 gap hypotheses in needs_review status (never auto-approved)."""
    if body.gap_class not in VALID_GAP_CLASSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid gap_class. Expected one of: {sorted(VALID_GAP_CLASSES)}",
        )

    # Discern before write — hard_fail blocks creation
    discern_raw = discern(
        artifact_type="gap_hypothesis",
        risk_tier="L2",
        cou=COU,
        input_payload={"program_id": body.program_id, "gap_class": body.gap_class},
        output_payload={
            "claim": body.claim,
            "confidence": body.confidence,
            "suggested_experiment": body.suggested_experiment,
            "insufficient_evidence": body.insufficient_evidence,
            "supported_by_trial_ids": body.supported_by_trial_ids,
            "supported_by_gene_ids": body.supported_by_gene_ids,
            "literature_refs": [r.model_dump() for r in body.literature_refs],
            "program_id": body.program_id,
        },
    )
    if discern_raw["action"] == "block":
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Discern hard_fail — hypothesis blocked (compliance/safety).",
                "discern": discern_raw,
            },
        )

    with get_session() as session:
        prog = session.run(
            "MATCH (p:Program {id: $id}) RETURN p.id AS id", id=body.program_id
        ).single()
        if not prog:
            raise HTTPException(status_code=404, detail=f"Program not found: {body.program_id}")

        gap_id = body.id or f"gap-{uuid.uuid4().hex[:12]}"
        refs_json = json.dumps([r.model_dump() for r in body.literature_refs])
        has_structured = bool(body.supported_by_trial_ids or body.supported_by_gene_ids)
        has_lit = len(body.literature_refs) > 0
        insufficient = body.insufficient_evidence or not (has_structured and has_lit)
        phash = provenance_hash(gap_id, body.gap_class, body.claim, refs_json, body.program_id)

        # Clamp confidence when reliability soft-failed
        confidence = float(body.confidence)
        rel = (discern_raw.get("scores") or {}).get("reliability") or {}
        if isinstance(rel, dict) and not rel.get("passed", True):
            confidence = min(confidence, max(float(rel.get("score", 0.5)), 0.2))

        session.run(
            """
            MERGE (g:GapHypothesis {id: $id})
            SET g.gap_class = $gap_class,
                g.claim = $claim,
                g.confidence = $confidence,
                g.suggested_experiment = $suggested_experiment,
                g.status = 'needs_review',
                g.insufficient_evidence = $insufficient_evidence,
                g.provenance_hash = $provenance_hash,
                g.risk_tier = 'L2',
                g.cou = $cou,
                g.literature_refs_json = $literature_refs_json,
                g.discern_json = $discern_json
            WITH g
            MATCH (p:Program {id: $program_id})
            MERGE (g)-[:ABOUT]->(p)
            MERGE (g)-[:DERIVED_FROM]->(p)
            """,
            id=gap_id,
            gap_class=body.gap_class,
            claim=body.claim,
            confidence=confidence,
            suggested_experiment=body.suggested_experiment,
            insufficient_evidence=insufficient,
            provenance_hash=phash,
            cou=COU,
            literature_refs_json=refs_json,
            discern_json=json.dumps(discern_raw),
            program_id=body.program_id,
        )
        for tid in body.supported_by_trial_ids:
            session.run(
                """
                MATCH (g:GapHypothesis {id: $gap_id})
                MATCH (t:Trial {id: $trial_id})
                MERGE (g)-[:SUPPORTED_BY]->(t)
                """,
                gap_id=gap_id,
                trial_id=tid,
            )
        for gid in body.supported_by_gene_ids:
            session.run(
                """
                MATCH (g:GapHypothesis {id: $gap_id})
                OPTIONAL MATCH (gene:Gene {id: $gene_id})
                FOREACH (_ IN CASE WHEN gene IS NULL THEN [] ELSE [1] END |
                  MERGE (g)-[:SUPPORTED_BY]->(gene)
                )
                """,
                gap_id=gap_id,
                gene_id=gid,
            )

    detail = get_gap(gap_id)
    return ProposeGapsResponse(
        hypothesis=detail,
        message=(
            "Hypothesis created at L2 with status needs_review. "
            f"Discern action={discern_raw['action']} overall={discern_raw['overall']}. "
            "Human approval required before export as team conclusion."
        ),
        cou=COU,
        discern=to_response(discern_raw).model_dump(),
    )


@router.post("/{gap_id}/critic", response_model=CriticResponse)
def run_critic(gap_id: str, body: CriticRequest | None = None) -> CriticResponse:
    """Adversarial critic: attach counter-notes and optionally clamp confidence."""
    body = body or CriticRequest()
    with get_session() as session:
        row = session.run(
            """
            MATCH (g:GapHypothesis {id: $id})-[:ABOUT]->(p:Program)
            OPTIONAL MATCH (g)-[:SUPPORTED_BY]->(t:Trial)
            RETURN g, p.stall_summary AS stall, collect(t.outcome_summary) AS outcomes
            """,
            id=gap_id,
        ).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Gap hypothesis not found: {gap_id}")

        g = dict(row["g"])
        claim = g.get("claim") or ""
        confidence = float(g.get("confidence") or 0.5)
        notes: list[str] = []

        if g.get("insufficient_evidence"):
            notes.append("Flagged insufficient_evidence — dual-channel rule not fully satisfied.")
            confidence = min(confidence, 0.4)

        outcomes = [o for o in (row["outcomes"] or []) if o]
        if outcomes and "not met" in " ".join(outcomes).lower():
            notes.append(
                "Supporting trial outcome already reports primary endpoint miss — "
                "ensure hypothesis is explanatory, not a restate of failure alone."
            )

        if "causal" in claim.lower() or "proves" in claim.lower():
            notes.append("Claim language appears over-strong; clamp confidence and require softer wording.")
            confidence = min(confidence, 0.45)

        if body.extra_counter_evidence:
            notes.append(f"Reviewer-supplied counter-evidence: {body.extra_counter_evidence}")
            confidence = min(confidence, confidence * 0.9)

        if not notes:
            notes.append(
                "No hard contradictions found in local graph; still requires human scientific review before approval."
            )

        critic_notes = " | ".join(notes)

        discern_raw = discern(
            artifact_type="gap_hypothesis",
            risk_tier=g.get("risk_tier") or "L2",
            cou=g.get("cou") or COU,
            output_payload={
                "claim": claim,
                "confidence": confidence,
                "critic_notes": critic_notes,
                "insufficient_evidence": bool(g.get("insufficient_evidence")),
                "provenance_hash": g.get("provenance_hash"),
                "literature_refs": parse_json_list(g.get("literature_refs_json")),
                "program_id": None,
            },
        )
        if discern_raw["action"] == "block":
            confidence = min(confidence, 0.2)
            notes.append("Discern hard_fail — confidence clamped; do not approve without remediation.")
            critic_notes = " | ".join(notes)
            discern_raw = discern(
                artifact_type="gap_hypothesis",
                risk_tier=g.get("risk_tier") or "L2",
                cou=g.get("cou") or COU,
                output_payload={
                    "claim": claim,
                    "confidence": confidence,
                    "critic_notes": critic_notes,
                    "insufficient_evidence": True,
                    "provenance_hash": g.get("provenance_hash"),
                    "literature_refs": parse_json_list(g.get("literature_refs_json")),
                },
            )

        # Link program stall summary as soft contradiction context node if present
        session.run(
            """
            MATCH (g:GapHypothesis {id: $id})
            SET g.critic_notes = $critic_notes,
                g.critic_confidence = $critic_confidence,
                g.confidence = CASE
                  WHEN $critic_confidence < g.confidence THEN $critic_confidence
                  ELSE g.confidence
                END,
                g.status = CASE WHEN g.status = 'approved' THEN 'needs_review' ELSE g.status END,
                g.discern_json = $discern_json
            """,
            id=gap_id,
            critic_notes=critic_notes,
            critic_confidence=confidence,
            discern_json=json.dumps(discern_raw),
        )

        # Optional: mark trial as CONTRADICTED_BY when critic finds overclaim
        if body.link_trial_as_contradiction:
            session.run(
                """
                MATCH (g:GapHypothesis {id: $gap_id})
                MATCH (t:Trial {id: $trial_id})
                MERGE (g)-[:CONTRADICTED_BY]->(t)
                """,
                gap_id=gap_id,
                trial_id=body.link_trial_as_contradiction,
            )

    return CriticResponse(
        gap_id=gap_id,
        critic_notes=critic_notes,
        confidence_after=confidence,
        status="needs_review",
        cou=COU,
        ran_at=datetime.now(timezone.utc).isoformat(),
        discern=to_response(discern_raw).model_dump(),
    )
