"""Load processed CSV data into Neo4j."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.config import settings  # noqa: E402
from app.identifiers import validate_association  # noqa: E402

INIT_CYPHER = (ROOT / "scripts" / "neo4j" / "init.cypher").read_text(encoding="utf-8")
ASSOC_PATH = ROOT / "data" / "processed" / "associations.csv"
BATCH_SIZE = 1000


def run_constraints(session) -> None:
    for stmt in INIT_CYPHER.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            session.run(stmt)


def _optional_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def seed(driver, *, strict: bool = False) -> None:
    assoc = pd.read_csv(ASSOC_PATH)
    warning_count = 0
    for _, row in assoc.iterrows():
        for warning in validate_association(row.to_dict(), strict=strict):
            warning_count += 1
            if warning_count <= 10:
                print(f"  warn: {warning}")
    if warning_count:
        print(f"Identifier validation: {warning_count} warning(s) before seed")
    proteins_path = ROOT / "data" / "processed" / "proteins.csv"
    proteins = pd.read_csv(proteins_path) if proteins_path.exists() else pd.DataFrame()

    with driver.session() as session:
        run_constraints(session)
        session.run("MATCH (n) DETACH DELETE n")

        for _, row in assoc.drop_duplicates(subset=["target_id"]).iterrows():
            session.run(
                """
                MERGE (g:Gene {id: $id})
                SET g.symbol = $symbol, g.name = $name
                """,
                id=row["target_id"],
                symbol=row["symbol"],
                name=row["name"],
            )

        for _, row in assoc.drop_duplicates(subset=["disease_id"]).iterrows():
            session.run(
                """
                MERGE (d:Disease {id: $id})
                SET d.name = $name
                """,
                id=row["disease_id"],
                name=row["disease_name"],
            )

        assoc_rows = assoc.to_dict("records")
        for start in range(0, len(assoc_rows), BATCH_SIZE):
            batch = []
            for row in assoc_rows[start : start + BATCH_SIZE]:
                evidence_json = row.get("evidence_json", "[]")
                if pd.isna(evidence_json):
                    evidence_json = "[]"
                batch.append(
                    {
                        "target_id": row["target_id"],
                        "disease_id": row["disease_id"],
                        "score": float(row["score"]),
                        "source": row.get("source", "opentargets"),
                        "evidence_type": row.get("evidence_type", "genetic_association"),
                        "evidence_json": str(evidence_json),
                        "study_id": _optional_str(row.get("study_id")),
                    }
                )
            session.run(
                """
                UNWIND $rows AS row
                MATCH (g:Gene {id: row.target_id})
                MATCH (d:Disease {id: row.disease_id})
                MERGE (g)-[r:ASSOCIATED_WITH]->(d)
                SET r.score = row.score,
                    r.source = row.source,
                    r.evidence_type = row.evidence_type,
                    r.evidence_json = row.evidence_json,
                    r.study_id = row.study_id
                """,
                rows=batch,
            )
            if (start // BATCH_SIZE) % 50 == 0 and start:
                print(f"  associations: {start}/{len(assoc_rows)}...")

        for _, row in proteins.iterrows():
            session.run(
                """
                MERGE (p:Protein {id: $id})
                SET p.name = $name
                WITH p
                MATCH (g:Gene {id: $gene_id})
                MERGE (p)-[:ENCODED_BY]->(g)
                """,
                id=row["id"],
                name=row["name"],
                gene_id=row["gene_id"],
            )

        counts = session.run(
            """
            RETURN
              count { (g:Gene) } AS genes,
              count { (d:Disease) } AS diseases,
              count { ()-[:ASSOCIATED_WITH]->() } AS associations
            """
        ).single()
        print(f"Seeded: {counts['genes']} genes, {counts['diseases']} diseases, {counts['associations']} associations")

    # GapForge case studies (programs / trials / hypotheses) — after associations
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from seed_gapforge import seed_gapforge  # noqa: E402

    seed_gapforge(driver)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Load processed CSV into Neo4j")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on invalid ENSG/EFO/MONDO ids (production bulk ingest)",
    )
    args = parser.parse_args()

    uri = os.getenv("NEO4J_URI", settings.neo4j_uri)
    user = os.getenv("NEO4J_USER", settings.neo4j_user)
    password = os.getenv("NEO4J_PASSWORD", settings.neo4j_password)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        seed(driver, strict=args.strict)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
