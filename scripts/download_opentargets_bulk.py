"""Download Open Targets Platform bulk association + evidence files (full ingest).

Documented source: https://platform-docs.opentargets.org/data-access/datasets
Default release: 24.06 (June 2024) from FTP.

Usage (requires network + disk; not run in CI):

    py -3 scripts/download_opentargets_bulk.py --release 24.06 --max-genes 500
    py -3 scripts/download_opentargets_bulk.py --release 24.06 --max-genes 500 --with-evidence
    py -3 scripts/attach_opentargets_evidence.py --input data/raw/opentargets_bulk.json --output data/raw/opentargets_bulk_evidence.json
    py -3 scripts/etl_opentargets.py --input data/raw/opentargets_bulk.json
    py -3 scripts/seed_neo4j.py

For CI and quick local dev, use the frozen slice instead:

    py -3 scripts/build_frozen_slice.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
sys.path.insert(0, str(ROOT / "scripts"))

from opentargets_ftp import attach_evidence, ftp_dir_url, iter_json_lines


def _target_id(row: dict) -> str | None:
    return row.get("targetId") or row.get("target_id")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Open Targets bulk slice")
    parser.add_argument("--release", default="24.06", help="Open Targets release folder, e.g. 24.06")
    parser.add_argument("--max-genes", type=int, default=500, help="Cap unique targets in output JSON")
    parser.add_argument(
        "--with-evidence",
        action="store_true",
        help="Attach typed evidence rows from Open Targets evidence shards (slower)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RAW_DIR / "opentargets_bulk.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    assoc_dir_url = ftp_dir_url(args.release, "associationByOverallDirect")
    print(f"Fetching associations from {assoc_dir_url} (sharded JSON parts; may take several minutes)...")

    allowed: set[str] = set()
    associations: list[dict] = []
    try:
        for row in iter_json_lines(assoc_dir_url, label="associations"):
            target = _target_id(row)
            if not target:
                continue
            if target not in allowed and len(allowed) >= args.max_genes:
                continue
            if target not in allowed:
                allowed.add(target)
            disease = row.get("diseaseId") or row.get("disease_id")
            score = row.get("score") or row.get("associationScore") or 0.0
            associations.append(
                {
                    "target_id": target,
                    "symbol": row.get("targetSymbol", target),
                    "name": row.get("targetName", target),
                    "disease_id": disease,
                    "disease_name": row.get("diseaseName", disease),
                    "score": float(score),
                    "source": "opentargets",
                    "evidence_type": "genetic_association",
                    "evidence": [
                        {
                            "evidence_type": "genetic_association",
                            "source": "opentargets",
                            "score": float(score),
                        }
                    ],
                }
            )
    except Exception as exc:
        print(
            "Bulk download failed. Use the frozen slice for offline/CI workflows:\n"
            "  py -3 scripts/build_frozen_slice.py\n"
            f"Error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    if args.with_evidence:
        print("Attaching typed evidence from Open Targets evidence shards...")
        attached = attach_evidence(associations, release=args.release, allowed_genes=allowed)
        print(f"Attached {attached} evidence row(s) across {len(associations)} associations")

    payload = {
        "meta": {
            "data_version": f"opentargets-{args.release}-bulk"
            + ("-evidence" if args.with_evidence else ""),
            "source": "opentargets-ftp",
            "release": args.release,
        },
        "associations": associations,
        "proteins": [],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(associations)} associations for {len(allowed)} genes -> {args.output}"
    )


if __name__ == "__main__":
    main()
