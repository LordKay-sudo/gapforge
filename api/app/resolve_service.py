"""Canonical entity resolution for genes and diseases (ontology-aware)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

ENSG_INPUT_RE = re.compile(r"^ENSG\d{11}$", re.IGNORECASE)
DISEASE_INPUT_RE = re.compile(r"^(EFO|MONDO)_\d+$", re.IGNORECASE)


class EntityType(str, Enum):
    GENE = "gene"
    DISEASE = "disease"


@dataclass(frozen=True)
class Candidate:
    id: str
    label: str


def disease_id_system(disease_id: str) -> str:
    if disease_id.startswith("EFO_"):
        return "EFO"
    if disease_id.startswith("MONDO_"):
        return "MONDO"
    return "disease_id"


def pick_best(query: str, candidates: list[Candidate]) -> Candidate:
    upper = query.upper()
    for candidate in candidates:
        if candidate.label.upper() == upper or candidate.id.upper() == upper:
            return candidate
    return candidates[0]


def ambiguity_list(query: str, all_candidates: list[Candidate], best: Candidate) -> list[Candidate]:
    if len(all_candidates) <= 1:
        return []
    others = [c for c in all_candidates if c.id != best.id]
    if best.label.upper() == query.upper() and len(others) == len(all_candidates) - 1:
        return others[:4]
    return others[:4]


def build_gene_resolution(query: str, candidates: list[Candidate]) -> dict:
    best = pick_best(query, candidates)
    ambiguous = ambiguity_list(query, candidates, best)
    note = (
        "Single best match from gene search."
        if not ambiguous
        else "Multiple matches — confirm symbol before dossier."
    )
    return {
        "entity_type": "gene",
        "canonical_id": best.id,
        "id_system": "ENSG",
        "symbol": best.label,
        "ambiguous": bool(ambiguous),
        "resolution_note": note,
        "candidates": [{"id": c.id, "label": c.label} for c in ambiguous],
    }


def build_disease_resolution(query: str, candidates: list[Candidate]) -> dict:
    best = pick_best(query, candidates)
    ambiguous = ambiguity_list(query, candidates, best)
    note = (
        "Single best match from disease search."
        if not ambiguous
        else "Multiple disease matches — confirm id before get_disease_genes."
    )
    return {
        "entity_type": "disease",
        "canonical_id": best.id,
        "id_system": disease_id_system(best.id),
        "name": best.label,
        "ambiguous": bool(ambiguous),
        "resolution_note": note,
        "candidates": [{"id": c.id, "label": c.label} for c in ambiguous],
    }


def resolved_gene_id(query: str) -> dict | None:
    if not ENSG_INPUT_RE.match(query):
        return None
    canonical = query.upper()
    return {
        "entity_type": "gene",
        "canonical_id": canonical,
        "id_system": "ENSG",
        "symbol": canonical,
        "ambiguous": False,
        "resolution_note": "Input is already an Ensembl gene id.",
        "candidates": [],
    }


def resolved_disease_id(query: str) -> dict | None:
    if not DISEASE_INPUT_RE.match(query):
        return None
    prefix, suffix = query.split("_", 1)
    canonical = f"{prefix.upper()}_{suffix}"
    return {
        "entity_type": "disease",
        "canonical_id": canonical,
        "id_system": disease_id_system(canonical),
        "name": canonical,
        "ambiguous": False,
        "resolution_note": "Input is already a disease ontology id.",
        "candidates": [],
    }


def not_found(entity_type: EntityType, query: str) -> dict:
    label = entity_type.value
    return {
        "error": True,
        "entity_type": label,
        "detail": f"No {label} found for: {query}",
        "suggestion": f"Try a different spelling or use search_{'genes' if entity_type == EntityType.GENE else 'diseases'}",
    }


def search_gene_candidates(session, query: str) -> list[Candidate]:
    rows = session.run(
        """
        MATCH (g:Gene)
        WHERE g.id = $q
           OR toLower(g.symbol) = toLower($q)
           OR toLower(g.symbol) CONTAINS toLower($q)
           OR toLower(coalesce(g.name, '')) CONTAINS toLower($q)
        RETURN g.id AS id, g.symbol AS symbol, g.name AS name
        ORDER BY
          CASE
            WHEN g.id = $q THEN 0
            WHEN toLower(g.symbol) = toLower($q) THEN 1
            ELSE 2
          END,
          g.symbol
        LIMIT 25
        """,
        q=query,
    )
    return [
        Candidate(id=row["id"], label=row["symbol"] or row["name"] or row["id"])
        for row in rows
        if row["id"]
    ]


def search_disease_candidates(session, query: str) -> list[Candidate]:
    rows = session.run(
        """
        MATCH (d:Disease)
        WHERE d.id = $q
           OR toLower(d.name) = toLower($q)
           OR toLower(d.name) CONTAINS toLower($q)
           OR toLower(d.id) CONTAINS toLower($q)
        RETURN d.id AS id, d.name AS name
        ORDER BY
          CASE
            WHEN d.id = $q THEN 0
            WHEN toLower(d.name) = toLower($q) THEN 1
            ELSE 2
          END,
          d.name
        LIMIT 25
        """,
        q=query,
    )
    return [
        Candidate(id=row["id"], label=row["name"] or row["id"])
        for row in rows
        if row["id"]
    ]


def resolve(session, query: str, entity_type: EntityType) -> dict:
    q = (query or "").strip()
    if not q:
        return {"error": True, "detail": "Query is required."}

    if entity_type == EntityType.GENE:
        direct = resolved_gene_id(q)
        if direct:
            exists = session.run(
                "MATCH (g:Gene {id: $id}) RETURN g.symbol AS symbol LIMIT 1",
                id=direct["canonical_id"],
            ).single()
            if exists and exists.get("symbol"):
                direct["symbol"] = exists["symbol"]
            return direct

        candidates = search_gene_candidates(session, q)
        if not candidates:
            return not_found(entity_type, q)
        return build_gene_resolution(q, candidates)

    direct = resolved_disease_id(q)
    if direct:
        exists = session.run(
            "MATCH (d:Disease {id: $id}) RETURN d.name AS name LIMIT 1",
            id=direct["canonical_id"],
        ).single()
        if exists and exists.get("name"):
            direct["name"] = exists["name"]
        return direct

    candidates = search_disease_candidates(session, q)
    if not candidates:
        return not_found(entity_type, q)
    return build_disease_resolution(q, candidates)
