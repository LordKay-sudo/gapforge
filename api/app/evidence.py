"""Parse evidence payloads stored on ASSOCIATED_WITH relationships."""
from __future__ import annotations

import json
from typing import Any

from app.models.schemas import EvidenceItem


def parse_evidence_items(raw: Any) -> list[EvidenceItem]:
    if raw is None:
        return []
    if isinstance(raw, str):
        if not raw.strip():
            return []
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    items: list[EvidenceItem] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        evidence_type = row.get("evidence_type") or row.get("type")
        source = row.get("source")
        score = row.get("score")
        if evidence_type is None or source is None or score is None:
            continue
        items.append(
            EvidenceItem(
                evidence_type=str(evidence_type),
                source=str(source),
                score=float(score),
                study_id=row.get("study_id"),
            )
        )
    return items


def evidence_items_to_json(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, separators=(",", ":"))
