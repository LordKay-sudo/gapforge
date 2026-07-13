"""API routes for GapForge programs, dossiers, and taxonomy scores."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.db import get_session
from app.gapforge import COU, GAP_TAXONOMY, parse_json_list
from app.models.schemas import (
    DrugSummary,
    GapHypothesisSummary,
    ProgramDetail,
    ProgramDossier,
    ProgramSummary,
    ProgramTaxonomy,
    TaxonomyDimension,
    TrialSummary,
)

router = APIRouter(prefix="/programs", tags=["gapforge-programs"])


def _program_from_node(p: dict, *, drug: dict | None = None, trial_count: int = 0, gap_count: int = 0) -> ProgramSummary:
    return ProgramSummary(
        id=p["id"],
        name=p.get("name") or p["id"],
        status=p.get("status"),
        indication_name=p.get("indication_name"),
        moa=p.get("moa"),
        stall_summary=p.get("stall_summary"),
        drug_name=(drug or {}).get("name"),
        trial_count=trial_count,
        gap_count=gap_count,
    )


@router.get("", response_model=list[ProgramSummary])
def list_programs() -> list[ProgramSummary]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (p:Program)
            OPTIONAL MATCH (p)-[:INVESTIGATES]->(d:Drug)
            OPTIONAL MATCH (p)-[:TESTED_IN]->(t:Trial)
            OPTIONAL MATCH (g:GapHypothesis)-[:ABOUT]->(p)
            RETURN p, d,
                   count(DISTINCT t) AS trial_count,
                   count(DISTINCT g) AS gap_count
            ORDER BY p.name
            """
        )
        out: list[ProgramSummary] = []
        for row in rows:
            p = dict(row["p"])
            d = dict(row["d"]) if row["d"] else None
            out.append(
                _program_from_node(
                    p, drug=d, trial_count=row["trial_count"], gap_count=row["gap_count"]
                )
            )
        return out


@router.get("/{program_id}", response_model=ProgramDetail)
def get_program(program_id: str) -> ProgramDetail:
    with get_session() as session:
        row = session.run(
            """
            MATCH (p:Program {id: $id})
            OPTIONAL MATCH (p)-[:INVESTIGATES]->(d:Drug)
            OPTIONAL MATCH (p)-[:FOR_INDICATION]->(dis:Disease)
            OPTIONAL MATCH (p)-[:TARGETS]->(g:Gene)
            OPTIONAL MATCH (p)-[:TESTED_IN]->(t:Trial)
            OPTIONAL MATCH (gap:GapHypothesis)-[:ABOUT]->(p)
            RETURN p, d, dis,
                   collect(DISTINCT g {.id, .symbol, .name}) AS genes,
                   collect(DISTINCT t) AS trials,
                   collect(DISTINCT gap) AS gaps
            """,
            id=program_id,
        ).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Program not found: {program_id}")

        p = dict(row["p"])
        drug = None
        if row["d"]:
            dn = dict(row["d"])
            drug = DrugSummary(
                id=dn["id"],
                name=dn.get("name") or dn["id"],
                synonyms=list(dn.get("synonyms") or []),
                chembl_id=dn.get("chembl_id"),
            )
        disease = None
        if row["dis"]:
            disease = {"id": row["dis"]["id"], "name": row["dis"].get("name")}

        trials = [
            TrialSummary(
                id=dict(t)["id"],
                nct_id=dict(t).get("nct_id"),
                phase=dict(t).get("phase"),
                status=dict(t).get("status"),
                primary_endpoint=dict(t).get("primary_endpoint"),
                outcome_summary=dict(t).get("outcome_summary"),
                url=dict(t).get("url"),
            )
            for t in row["trials"]
            if t is not None
        ]
        gaps = [
            GapHypothesisSummary(
                id=dict(g)["id"],
                gap_class=dict(g).get("gap_class") or "efficacy",
                claim=dict(g).get("claim") or "",
                confidence=float(dict(g).get("confidence") or 0),
                status=dict(g).get("status") or "needs_review",
                risk_tier=dict(g).get("risk_tier") or "L2",
                insufficient_evidence=bool(dict(g).get("insufficient_evidence")),
                program_id=program_id,
                suggested_experiment=dict(g).get("suggested_experiment"),
                provenance_hash=dict(g).get("provenance_hash"),
                critic_notes=dict(g).get("critic_notes"),
                literature_refs=parse_json_list(dict(g).get("literature_refs_json")),
            )
            for g in row["gaps"]
            if g is not None
        ]
        genes = [g for g in row["genes"] if g and g.get("id")]

        return ProgramDetail(
            id=p["id"],
            name=p.get("name") or p["id"],
            status=p.get("status"),
            indication_name=p.get("indication_name"),
            moa=p.get("moa"),
            stall_summary=p.get("stall_summary"),
            cou_note=p.get("cou_note") or COU,
            case_study_id=p.get("case_study_id"),
            drug=drug,
            disease=disease,
            genes=genes,
            trials=trials,
            gaps=gaps,
            trial_count=len(trials),
            gap_count=len(gaps),
            drug_name=drug.name if drug else None,
        )


@router.get("/{program_id}/dossier", response_model=ProgramDossier)
def program_dossier(program_id: str) -> ProgramDossier:
    detail = get_program(program_id)
    return ProgramDossier(
        program=detail,
        cou=COU,
        risk_tier_note="Dossier is L1 summary; gap cards remain L2 and require HITL approval.",
        verify_ui_path=f"/program/{program_id}",
    )


@router.get("/{program_id}/taxonomy", response_model=ProgramTaxonomy)
def program_taxonomy(program_id: str) -> ProgramTaxonomy:
    with get_session() as session:
        row = session.run(
            "MATCH (p:Program {id: $id}) RETURN p.taxonomy_json AS taxonomy_json, p.name AS name",
            id=program_id,
        ).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Program not found: {program_id}")
        raw = {}
        if row["taxonomy_json"]:
            try:
                raw = json.loads(row["taxonomy_json"])
            except json.JSONDecodeError:
                raw = {}
        dimensions = []
        for code, label in GAP_TAXONOMY.items():
            # Map seed keys to taxonomy codes loosely
            key_map = {
                "target_validity": "target_validity",
                "patient_stratification": "biomarker",
                "endpoint_fitness": "endpoint",
                "exposure_pk": "pk_exposure",
                "safety_signals": "safety",
                "formulation_delivery": "formulation",
                "competitive_soc": "competitive",
            }
            score = None
            for seed_key, tax_code in key_map.items():
                if tax_code == code and seed_key in raw:
                    score = float(raw[seed_key])
            if score is None and code in raw:
                score = float(raw[code])
            dimensions.append(
                TaxonomyDimension(
                    code=code,
                    label=label,
                    evidence_density=score if score is not None else 0.5,
                )
            )
        return ProgramTaxonomy(
            program_id=program_id,
            program_name=row["name"] or program_id,
            dimensions=dimensions,
            note="Evidence density is a curated demo score (0–1); higher means more supporting public evidence assembled, not clinical truth.",
        )
