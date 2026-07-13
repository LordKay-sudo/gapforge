"""Attach Open Targets evidence shards to an existing bulk associations JSON.

Skips re-downloading association parts — use after download_opentargets_bulk.py.
Checkpoints after each evidence source so a failed run can resume.

Usage:
    py -3 -u scripts/attach_opentargets_evidence.py \\
        --input data/raw/opentargets_bulk.json \\
        --output data/raw/opentargets_bulk_evidence.json

Resume after interruption:
    py -3 -u scripts/attach_opentargets_evidence.py ... --resume
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from opentargets_ftp import (
    DEFAULT_EVIDENCE_SOURCES,
    attach_evidence_source,
    finalize_evidence_metadata,
)


def _write_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach OT evidence to bulk JSON")
    parser.add_argument("--input", type=Path, required=True, help="Existing bulk JSON")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--release", default="24.06", help="Open Targets release")
    parser.add_argument("--resume", action="store_true", help="Resume from partial output")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=None,
        help=f"Evidence source ids (default: {', '.join(DEFAULT_EVIDENCE_SOURCES)})",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    sources = args.sources or list(DEFAULT_EVIDENCE_SOURCES)
    completed: list[str] = []
    data: dict

    if args.resume and args.output.exists():
        data = json.loads(args.output.read_text(encoding="utf-8"))
        completed = list(data.get("meta", {}).get("evidence_sources_completed") or [])
        print(f"Resuming — {len(completed)} source(s) already done: {', '.join(completed)}", flush=True)
    else:
        data = json.loads(args.input.read_text(encoding="utf-8"))

    associations: list[dict] = data.get("associations") or []
    if not associations:
        raise SystemExit("No associations in input JSON")

    allowed_genes = {a["target_id"] for a in associations}
    release = data.get("meta", {}).get("release") or args.release
    meta = dict(data.get("meta") or {})
    meta.setdefault("data_version", f"opentargets-{release}-bulk")
    if not str(meta["data_version"]).endswith("-evidence"):
        meta["data_version"] = f"{meta['data_version']}-evidence"

    print(
        f"Attaching evidence for {len(associations)} associations ({len(allowed_genes)} genes)...",
        flush=True,
    )

    total_attached = int(meta.get("evidence_rows_attached") or 0)
    for source_name in sources:
        if source_name in completed:
            print(f"  skip completed source {source_name}", flush=True)
            continue
        attached = attach_evidence_source(
            associations,
            release=release,
            allowed_genes=allowed_genes,
            source_name=source_name,
        )
        total_attached += attached
        completed.append(source_name)
        meta["evidence_sources_completed"] = completed
        meta["evidence_rows_attached"] = total_attached
        finalize_evidence_metadata(associations)
        payload = {**data, "meta": meta, "associations": associations}
        _write_payload(args.output, payload)
        print(f"  checkpoint {source_name}: +{attached} rows (total {total_attached})", flush=True)

    print(f"Attached {total_attached} evidence row(s) -> {args.output}", flush=True)


if __name__ == "__main__":
    main()
