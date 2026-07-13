"""GapForge constants and small helpers."""
from __future__ import annotations

import hashlib
import json
from typing import Any

COU = (
    "Generate literature-backed gap hypotheses for scientific discussion; "
    "not for clinical care or regulatory submission."
)

GAP_TAXONOMY: dict[str, str] = {
    "efficacy": "Lack of clinical efficacy",
    "safety": "Safety / toxicity",
    "pk_exposure": "PK / bioavailability / exposure",
    "formulation": "Formulation / delivery",
    "biomarker": "Stratification / predictive biomarker",
    "endpoint": "Endpoint / surrogate mismatch",
    "target_validity": "Target / biological hypothesis validity",
    "competitive": "Competitive / SoC (extrinsic)",
}

VALID_GAP_CLASSES = frozenset(GAP_TAXONOMY.keys())
VALID_REVIEW_STATUSES = frozenset({"draft", "needs_review", "approved", "rejected"})
VALID_REVIEW_DECISIONS = frozenset({"approve", "reject", "request_more"})


def provenance_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()[:16]


def parse_json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except json.JSONDecodeError:
        return []
