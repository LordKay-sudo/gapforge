"""OntoHarness validation helpers for GapForge L2 gates."""
from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.ontology_rdf import gap_hypothesis_to_turtle
from app.ontoharness_client import blocks_approval, validate_turtle


def validate_gap_hypothesis(
    gap: dict,
    genes: list[dict] | None,
    disease: dict | None,
) -> dict[str, Any]:
    if not settings.ontoharness_enabled:
        return {"conforms": True, "skipped": True, "reason": "ontoharness_disabled"}

    turtle = gap_hypothesis_to_turtle(
        gap_id=gap.get("id") or "gap-unknown",
        claim=gap.get("claim") or "",
        confidence=float(gap.get("confidence") or 0),
        genes=genes,
        disease=disease,
    )
    result = validate_turtle(turtle)
    result["turtle_preview"] = turtle
    return result


def persist_validation_json(result: dict[str, Any]) -> str:
    return json.dumps({k: v for k, v in result.items() if k != "turtle_preview"})
