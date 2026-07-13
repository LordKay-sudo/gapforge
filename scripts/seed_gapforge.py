"""Seed GapForge program/trial/hypothesis nodes into Neo4j (after associations seed)."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.config import settings  # noqa: E402

INIT_CYPHER = (ROOT / "scripts" / "neo4j" / "init.cypher").read_text(encoding="utf-8")
CASE_PATH = ROOT / "data" / "gapforge" / "flurizan_case.json"
COU = (
    "Generate literature-backed gap hypotheses for scientific discussion; "
    "not for clinical care or regulatory submission."
)


def run_constraints(session) -> None:
    for stmt in INIT_CYPHER.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            session.run(stmt)


def provenance_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()[:16]


def seed_gapforge(driver) -> None:
    data = json.loads(CASE_PATH.read_text(encoding="utf-8"))
    drug = data["drug"]
    program = data["program"]
    trials = data["trials"]
    hypotheses = data["hypotheses"]
    taxonomy = data.get("taxonomy_seed", {})

    with driver.session() as session:
        run_constraints(session)

        session.run(
            """
            MERGE (d:Drug {id: $id})
            SET d.name = $name,
                d.synonyms = $synonyms,
                d.chembl_id = $chembl_id
            """,
            id=drug["id"],
            name=drug["name"],
            synonyms=drug.get("synonyms", []),
            chembl_id=drug.get("chembl_id"),
        )

        session.run(
            """
            MERGE (p:Program {id: $id})
            SET p.name = $name,
                p.status = $status,
                p.indication_name = $indication_name,
                p.moa = $moa,
                p.cou_note = $cou_note,
                p.stall_summary = $stall_summary,
                p.case_study_id = $case_study_id,
                p.taxonomy_json = $taxonomy_json
            """,
            id=program["id"],
            name=program["name"],
            status=program["status"],
            indication_name=program["indication_name"],
            moa=program["moa"],
            cou_note=program.get("cou_note", COU),
            stall_summary=program.get("stall_summary", ""),
            case_study_id=data["case_study"]["id"],
            taxonomy_json=json.dumps(taxonomy),
        )

        session.run(
            """
            MATCH (p:Program {id: $program_id})
            MATCH (d:Drug {id: $drug_id})
            MERGE (p)-[:INVESTIGATES]->(d)
            """,
            program_id=program["id"],
            drug_id=drug["id"],
        )

        # Link indication disease if present in graph
        session.run(
            """
            MATCH (p:Program {id: $program_id})
            OPTIONAL MATCH (dis:Disease {id: $disease_id})
            FOREACH (_ IN CASE WHEN dis IS NULL THEN [] ELSE [1] END |
              MERGE (p)-[:FOR_INDICATION]->(dis)
            )
            """,
            program_id=program["id"],
            disease_id=program["disease_id"],
        )

        for gene_id in program.get("gene_ids", []):
            session.run(
                """
                MATCH (p:Program {id: $program_id})
                OPTIONAL MATCH (g:Gene {id: $gene_id})
                FOREACH (_ IN CASE WHEN g IS NULL THEN [] ELSE [1] END |
                  MERGE (p)-[:TARGETS]->(g)
                )
                """,
                program_id=program["id"],
                gene_id=gene_id,
            )

        for trial in trials:
            session.run(
                """
                MERGE (t:Trial {id: $id})
                SET t.nct_id = $nct_id,
                    t.phase = $phase,
                    t.status = $status,
                    t.primary_endpoint = $primary_endpoint,
                    t.outcome_summary = $outcome_summary,
                    t.url = $url
                """,
                id=trial["id"],
                nct_id=trial["nct_id"],
                phase=trial["phase"],
                status=trial["status"],
                primary_endpoint=trial["primary_endpoint"],
                outcome_summary=trial["outcome_summary"],
                url=trial.get("url"),
            )
            session.run(
                """
                MATCH (p:Program {id: $program_id})
                MATCH (t:Trial {id: $trial_id})
                MERGE (p)-[:TESTED_IN]->(t)
                """,
                program_id=program["id"],
                trial_id=trial["id"],
            )
            session.run(
                """
                MATCH (t:Trial {id: $trial_id})
                OPTIONAL MATCH (dis:Disease {id: $disease_id})
                FOREACH (_ IN CASE WHEN dis IS NULL THEN [] ELSE [1] END |
                  MERGE (t)-[:FOR_INDICATION]->(dis)
                )
                """,
                trial_id=trial["id"],
                disease_id=trial.get("disease_id", program["disease_id"]),
            )

        for hyp in hypotheses:
            refs_json = json.dumps(hyp.get("literature_refs", []))
            phash = provenance_hash(
                hyp["id"], hyp["gap_class"], hyp["claim"], refs_json, program["id"]
            )
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
                    g.critic_notes = null,
                    g.critic_confidence = null
                """,
                id=hyp["id"],
                gap_class=hyp["gap_class"],
                claim=hyp["claim"],
                confidence=float(hyp["confidence"]),
                suggested_experiment=hyp["suggested_experiment"],
                insufficient_evidence=bool(hyp.get("insufficient_evidence", False)),
                provenance_hash=phash,
                cou=COU,
                literature_refs_json=refs_json,
            )
            session.run(
                """
                MATCH (g:GapHypothesis {id: $gap_id})
                MATCH (p:Program {id: $program_id})
                MERGE (g)-[:ABOUT]->(p)
                MERGE (g)-[:DERIVED_FROM]->(p)
                """,
                gap_id=hyp["id"],
                program_id=program["id"],
            )
            for tid in hyp.get("supported_by_trials", []):
                session.run(
                    """
                    MATCH (g:GapHypothesis {id: $gap_id})
                    MATCH (t:Trial {id: $trial_id})
                    MERGE (g)-[:SUPPORTED_BY]->(t)
                    MERGE (g)-[:DERIVED_FROM]->(t)
                    """,
                    gap_id=hyp["id"],
                    trial_id=tid,
                )
            for tid in hyp.get("contradicted_by_trials", []):
                session.run(
                    """
                    MATCH (g:GapHypothesis {id: $gap_id})
                    MATCH (t:Trial {id: $trial_id})
                    MERGE (g)-[:CONTRADICTED_BY]->(t)
                    """,
                    gap_id=hyp["id"],
                    trial_id=tid,
                )
            for gid in hyp.get("supported_by_genes", []):
                session.run(
                    """
                    MATCH (g:GapHypothesis {id: $gap_id})
                    OPTIONAL MATCH (gene:Gene {id: $gene_id})
                    FOREACH (_ IN CASE WHEN gene IS NULL THEN [] ELSE [1] END |
                      MERGE (g)-[:SUPPORTED_BY]->(gene)
                    )
                    """,
                    gap_id=hyp["id"],
                    gene_id=gid,
                )

        counts = session.run(
            """
            RETURN
              count { (p:Program) } AS programs,
              count { (t:Trial) } AS trials,
              count { (g:GapHypothesis) } AS gaps,
              count { (d:Drug) } AS drugs
            """
        ).single()
        print(
            f"GapForge seeded: {counts['programs']} programs, {counts['trials']} trials, "
            f"{counts['gaps']} gaps, {counts['drugs']} drugs"
        )


def main() -> None:
    uri = os.getenv("NEO4J_URI", settings.neo4j_uri)
    user = os.getenv("NEO4J_USER", settings.neo4j_user)
    password = os.getenv("NEO4J_PASSWORD", settings.neo4j_password)
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        seed_gapforge(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
