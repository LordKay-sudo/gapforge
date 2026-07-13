"""Ontology identifier validation for ingest (roadmap 2.1).

Genes must be Ensembl ENSG ids; diseases must be EFO/MONDO (or other ontology) ids.
Synthetic catalog placeholders (``OT####``/``GENE#``) are tolerated in the frozen demo
slice but flagged so production bulk ingest can enforce strict mode.
"""
from __future__ import annotations

import re

ENSG_RE = re.compile(r"^ENSG\d{11}$")
DISEASE_RE = re.compile(r"^(EFO|MONDO|HP|Orphanet|DOID|MP|NCIT)_\d+$")
PLACEHOLDER_GENE_RE = re.compile(r"^(OT\d+|GENE\d+)$")


class IdentifierError(ValueError):
    """Raised when an identifier fails validation in strict mode."""


def is_valid_gene_id(gene_id: str) -> bool:
    return bool(ENSG_RE.match(gene_id or ""))


def is_placeholder_gene_id(gene_id: str) -> bool:
    return bool(PLACEHOLDER_GENE_RE.match(gene_id or ""))


def is_valid_disease_id(disease_id: str) -> bool:
    return bool(DISEASE_RE.match(disease_id or ""))


def validate_association(row: dict, *, strict: bool = False) -> list[str]:
    """Return a list of validation warnings for one association row.

    In strict mode, an invalid id raises :class:`IdentifierError`. Placeholder gene
    ids (frozen-slice scaling) are always warnings, never strict failures.
    """
    warnings: list[str] = []
    gene_id = str(row.get("target_id", ""))
    disease_id = str(row.get("disease_id", ""))

    if not is_valid_gene_id(gene_id):
        if is_placeholder_gene_id(gene_id):
            warnings.append(f"placeholder gene id (demo slice): {gene_id}")
        else:
            msg = f"invalid gene id (expected ENSG#########): {gene_id}"
            if strict:
                raise IdentifierError(msg)
            warnings.append(msg)

    if not is_valid_disease_id(disease_id):
        msg = f"invalid disease id (expected EFO/MONDO/...): {disease_id}"
        if strict:
            raise IdentifierError(msg)
        warnings.append(msg)

    return warnings
