"""HITL review queue and provenance export for GapForge."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app import metadata
from app.db import get_session
from app.gapforge import COU, VALID_REVIEW_DECISIONS
from app.models.schemas import (
    GapHypothesisSummary,
    ReviewBundle,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewQueueItem,
)
from app.routers.gaps import _hyp_summary, get_gap
from app.routers.programs import get_program

router = APIRouter(tags=["gapforge-reviews"])


@router.get("/reviews/queue", response_model=list[ReviewQueueItem])
def review_queue(
    status: str = Query("needs_review", description="Filter by hypothesis status"),
) -> list[ReviewQueueItem]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (g:GapHypothesis)-[:ABOUT]->(p:Program)
            WHERE g.status = $status
            RETURN g, p.id AS program_id, p.name AS program_name
            ORDER BY g.confidence DESC
            """,
            status=status,
        )
        items: list[ReviewQueueItem] = []
        for row in rows:
            g = dict(row["g"])
            items.append(
                ReviewQueueItem(
                    hypothesis=_hyp_summary(g, row["program_id"]),
                    program_id=row["program_id"],
                    program_name=row["program_name"],
                    verify_ui_path=f"/program/{row['program_id']}",
                )
            )
        return items


@router.post("/reviews/{gap_id}", response_model=ReviewDecisionResponse)
def decide_review(gap_id: str, body: ReviewDecisionRequest) -> ReviewDecisionResponse:
    if body.decision not in VALID_REVIEW_DECISIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Expected one of: {sorted(VALID_REVIEW_DECISIONS)}",
        )
    status_map = {
        "approve": "approved",
        "reject": "rejected",
        "request_more": "needs_review",
    }
    new_status = status_map[body.decision]
    review_id = f"review-{uuid4().hex[:12]}"
    decided_at = datetime.now(timezone.utc).isoformat()

    with get_session() as session:
        exists = session.run(
            "MATCH (g:GapHypothesis {id: $id}) RETURN g.id AS id", id=gap_id
        ).single()
        if not exists:
            raise HTTPException(status_code=404, detail=f"Gap hypothesis not found: {gap_id}")

        session.run(
            """
            MATCH (g:GapHypothesis {id: $gap_id})
            SET g.status = $status
            MERGE (r:Review {id: $review_id})
            SET r.decision = $decision,
                r.reviewer = $reviewer,
                r.notes = $notes,
                r.decided_at = $decided_at
            MERGE (r)-[:REVIEWS]->(g)
            """,
            gap_id=gap_id,
            status=new_status,
            review_id=review_id,
            decision=body.decision,
            reviewer=body.reviewer or "anonymous",
            notes=body.notes or "",
            decided_at=decided_at,
        )

    return ReviewDecisionResponse(
        gap_id=gap_id,
        review_id=review_id,
        decision=body.decision,
        status=new_status,
        reviewer=body.reviewer or "anonymous",
        decided_at=decided_at,
        message=(
            "Approved — eligible for team-conclusion export."
            if body.decision == "approve"
            else (
                "Rejected — will not export as team conclusion."
                if body.decision == "reject"
                else "More evidence requested — remains in review queue."
            )
        ),
        cou=COU,
    )


@router.get("/export/review-bundle", response_model=ReviewBundle)
def export_review_bundle(
    gap_id: str | None = None,
    program_id: str | None = None,
) -> ReviewBundle:
    """Provenance bundle for audit — only includes approved gaps as team_conclusions."""
    if not gap_id and not program_id:
        raise HTTPException(status_code=400, detail="Provide gap_id and/or program_id")

    hypotheses: list[GapHypothesisSummary] = []
    program = None
    team_conclusions: list[GapHypothesisSummary] = []

    if gap_id:
        detail = get_gap(gap_id)
        hypotheses.append(GapHypothesisSummary(**{
            k: getattr(detail, k)
            for k in GapHypothesisSummary.model_fields
        }))
        program_id = program_id or detail.program_id
        if detail.status == "approved":
            team_conclusions.append(hypotheses[0])

    if program_id:
        program = get_program(program_id)
        if not gap_id:
            for g in program.gaps:
                hypotheses.append(g)
                if g.status == "approved":
                    team_conclusions.append(g)

    return ReviewBundle(
        exported_at=datetime.now(timezone.utc).isoformat(),
        cou=COU,
        data_version=metadata.DATA_VERSION,
        api_version=metadata.API_VERSION,
        program_id=program_id,
        program_name=program.name if program else None,
        hypotheses=hypotheses,
        team_conclusions=team_conclusions,
        disclaimer=metadata.DISCLAIMER,
        note=(
            "team_conclusions only lists approved L2 cards. "
            "Draft/needs_review/rejected cards are audit-visible but not team conclusions."
        ),
        raw_meta={
            "sources": metadata.SOURCES,
            "gapforge_doc": "docs/GAPFORGE.md",
        },
    )
