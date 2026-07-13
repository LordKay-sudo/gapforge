"""Shared Open Targets FTP helpers (sharded JSON listings and streaming)."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

FTP_BASE = "https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/{release}/output/etl/json"

DEFAULT_EVIDENCE_SOURCES = (
    "chembl",
    "europepmc",
    "ot_genetics_portal",
    "expression_atlas",
    "impc",
    "eva",
    "gene_burden",
    "cancer_gene_census",
)


def ftp_dir_url(release: str, *parts: str) -> str:
    base = FTP_BASE.format(release=release).rstrip("/")
    suffix = "/".join(p.strip("/") for p in parts if p)
    return f"{base}/{suffix}/" if suffix else f"{base}/"


def evidence_source_dir(source: str) -> str:
    """Open Targets evidence FTP folders use ``sourceId=chembl`` style paths."""
    if source.startswith("sourceId="):
        return source.rstrip("/")
    return f"sourceId={source}"


def list_part_files(dir_url: str) -> list[str]:
    with urllib.request.urlopen(dir_url, timeout=120) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parts = sorted(set(re.findall(r'href="(part-[^"]+\.json)"', html)))
    if not parts:
        raise RuntimeError(f"No part-*.json files found at {dir_url}")
    return parts


def list_evidence_sources(release: str) -> list[str]:
    index_url = ftp_dir_url(release, "evidence")
    with urllib.request.urlopen(index_url, timeout=120) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return sorted(
        m.replace("/", "")
        for m in re.findall(r'href="(sourceId=[^"/]+)/?"', html)
    )


def iter_json_lines(dir_url: str, *, label: str | None = None) -> Iterator[dict]:
    for part in list_part_files(dir_url):
        if label:
            print(f"  {label}: {part}...", flush=True)
        part_url = f"{dir_url.rstrip('/')}/{part}"
        body = _read_url_with_retry(part_url)
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"  warn: skip malformed JSON line in {part}", flush=True)


def _read_url_with_retry(url: str, *, attempts: int = 3) -> str:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=600) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt + 1 < attempts:
                wait = 2 ** attempt
                print(f"  warn: retry {url} in {wait}s ({exc})", flush=True)
                time.sleep(wait)
    raise last_exc  # type: ignore[misc]


def evidence_item_from_row(row: dict) -> dict:
    item = {
        "evidence_type": row.get("datatypeId") or row.get("evidence_type") or "unknown",
        "source": row.get("datasourceId") or row.get("source") or "opentargets",
        "score": float(row.get("score") or 0.0),
    }
    study_id = row.get("studyId") or row.get("study_id") or row.get("id")
    if study_id:
        item["study_id"] = str(study_id)
    return item


def finalize_evidence_metadata(associations: list[dict]) -> None:
    for assoc in associations:
        evidence = assoc.get("evidence") or []
        if not evidence:
            continue
        primary = max(evidence, key=lambda e: e.get("score", 0))
        assoc["evidence_type"] = primary.get("evidence_type", "genetic_association")
        study_id = primary.get("study_id")
        if study_id:
            assoc["study_id"] = study_id


def attach_evidence_source(
    associations: list[dict],
    *,
    release: str,
    allowed_genes: set[str],
    source_name: str,
    max_per_pair: int = 25,
) -> int:
    """Attach evidence rows from one Open Targets source shard directory."""
    pair_index = {(a["target_id"], a["disease_id"]): a for a in associations}
    allowed_pairs = set(pair_index.keys())
    source_dir = evidence_source_dir(source_name)
    dir_url = ftp_dir_url(release, "evidence", source_dir)
    attached = 0

    try:
        rows = iter_json_lines(dir_url, label=source_dir)
    except Exception as exc:
        print(f"  skip {source_dir}: {exc}", flush=True)
        return 0

    for row in rows:
        target = row.get("targetId") or row.get("target_id")
        disease = row.get("diseaseId") or row.get("disease_id")
        if not target or not disease:
            continue
        if target not in allowed_genes:
            continue
        key = (target, disease)
        if key not in allowed_pairs:
            continue
        assoc = pair_index[key]
        evidence = assoc.setdefault("evidence", [])
        if len(evidence) >= max_per_pair:
            continue
        evidence.append(evidence_item_from_row(row))
        attached += 1

    return attached


def attach_evidence(
    associations: list[dict],
    *,
    release: str,
    allowed_genes: set[str],
    sources: list[str] | None = None,
    skip_sources: set[str] | None = None,
    max_per_pair: int = 25,
) -> int:
    """Merge Open Targets evidence shards into association dicts. Returns rows attached."""
    sources = sources or list(DEFAULT_EVIDENCE_SOURCES)
    skip_sources = skip_sources or set()
    attached = 0

    for source_name in sources:
        if source_name in skip_sources:
            print(f"  skip completed source {source_name}", flush=True)
            continue
        attached += attach_evidence_source(
            associations,
            release=release,
            allowed_genes=allowed_genes,
            source_name=source_name,
            max_per_pair=max_per_pair,
        )

    finalize_evidence_metadata(associations)
    return attached
