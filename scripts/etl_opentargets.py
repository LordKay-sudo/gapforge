"""Transform Open Targets–style JSON into processed CSV for seeding (ETL v2)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.evidence import evidence_items_to_json  # noqa: E402
from app.identifiers import validate_association  # noqa: E402
DEFAULT_RAW = ROOT / "data" / "raw" / "opentargets_slice_v2.json"
LEGACY_RAW = ROOT / "data" / "raw" / "opentargets_sample.json"
OUT_DIR = ROOT / "data" / "processed"


def _normalize_association(row: dict) -> dict:
    evidence = row.get("evidence") or []
    primary_type = row.get("evidence_type")
    if not primary_type and evidence:
        primary_type = max(evidence, key=lambda e: e.get("score", 0)).get("evidence_type")
    study_id = row.get("study_id")
    if not study_id and evidence:
        for item in evidence:
            if item.get("study_id"):
                study_id = item["study_id"]
                break
    return {
        "target_id": row["target_id"],
        "symbol": row["symbol"],
        "name": row["name"],
        "disease_id": row["disease_id"],
        "disease_name": row["disease_name"],
        "score": float(row["score"]),
        "source": row.get("source", "opentargets"),
        "evidence_type": primary_type or "genetic_association",
        "study_id": study_id,
        "evidence_json": evidence_items_to_json(evidence) if evidence else "[]",
    }


def transform(data: dict, *, strict: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = data["associations"]
    warning_count = 0
    for row in rows:
        for warning in validate_association(row, strict=strict):
            warning_count += 1
            if warning_count <= 10:
                print(f"  warn: {warning}")
    if warning_count:
        print(f"Identifier validation: {warning_count} warning(s) across {len(rows)} associations")
    associations = pd.DataFrame([_normalize_association(r) for r in rows])
    proteins = pd.DataFrame(data.get("proteins", []))
    return associations, proteins


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Targets JSON -> processed CSV")
    parser.add_argument("--input", type=Path, default=None, help="Raw JSON path")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on invalid ENSG/EFO/MONDO ids (production bulk ingest)",
    )
    args = parser.parse_args()

    raw_path = args.input or DEFAULT_RAW
    if not raw_path.exists():
        raw_path = LEGACY_RAW
    if not raw_path.exists():
        raise FileNotFoundError(
            f"No input JSON found. Run scripts/build_frozen_slice.py or scripts/download_opentargets_bulk.py. "
            f"Tried: {args.input or DEFAULT_RAW}, {LEGACY_RAW}"
        )

    with raw_path.open(encoding="utf-8") as f:
        data = json.load(f)

    associations, proteins = transform(data, strict=args.strict)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    associations.to_csv(OUT_DIR / "associations.csv", index=False)
    if not proteins.empty:
        proteins.to_csv(OUT_DIR / "proteins.csv", index=False)

    gene_count = associations["target_id"].nunique()
    print(
        f"Processed {len(associations)} associations across {gene_count} genes "
        f"from {raw_path.name}"
    )


if __name__ == "__main__":
    main()
