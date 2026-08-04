"""Build biomedical RDF for OntoHarness from GapForge hypothesis context."""
from __future__ import annotations

from xml.sax.saxutils import escape

XSD_DECIMAL = "<http://www.w3.org/2001/XMLSchema#decimal>"
XSD_DATETIME = "<http://www.w3.org/2001/XMLSchema#dateTime>"


def _lit(value: str) -> str:
    return f'"{escape(value)}"'


def _dec(value: float) -> str:
    return f'"{value}"^^{XSD_DECIMAL}'


def gap_hypothesis_to_turtle(
    gap_id: str,
    claim: str,
    confidence: float,
    genes: list[dict] | None = None,
    disease: dict | None = None,
    *,
    gap_class: str | None = None,
    approved_at: str | None = None,
    provenance_hash: str | None = None,
) -> str:
    """
    Minimal Turtle aligned with domains/biomedical in OntoHarness.
    genes: [{id, symbol}]
    disease: {id, name}
    """
    hyp_local = _safe_local(gap_id)
    hyp_lines = [
        f"bio:{hyp_local} a bio:Hypothesis ;",
        f"    rdfs:label {_lit(claim)} ;",
        f"    bio:confidence {_dec(max(0.0, min(1.0, float(confidence))))} ;",
    ]
    if gap_class:
        hyp_lines.append(f"    bio:gapClass {_lit(gap_class)} ;")
    if approved_at:
        hyp_lines.append(f'    bio:approvedAt "{escape(approved_at)}"^^{XSD_DATETIME} ;')
    if provenance_hash:
        hyp_lines.append(f"    bio:provenanceHash {_lit(provenance_hash)} ;")
    hyp_lines[-1] = hyp_lines[-1].rstrip(" ;") + " ."

    lines = [
        "@prefix bio: <https://ontoharness.dev/biomedical#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        *hyp_lines,
    ]

    score = max(0.0, min(1.0, float(confidence)))
    disease_local = _safe_local(disease["id"]) if disease and disease.get("id") else "disease-unknown"

    if disease and disease.get("id"):
        disease_lines = [
            "",
            f"bio:{disease_local} a bio:Disease ;",
            f"    bio:hasIdentifier {_lit(disease['id'])}",
        ]
        if disease.get("name"):
            disease_lines[-1] += " ;"
            disease_lines.append(f"    rdfs:label {_lit(disease['name'])} .")
        else:
            disease_lines[-1] += " ."
        lines.extend(disease_lines)

    for gene in genes or []:
        gid = gene.get("id") or gene.get("symbol") or "gene-unknown"
        symbol = gene.get("symbol") or gid
        glocal = _safe_local(gid)
        lines.extend(
            [
                "",
                f"bio:{glocal} a bio:Gene ;",
                f"    bio:hasSymbol {_lit(symbol)} ;",
                f"    bio:supports bio:{hyp_local} ;",
                f"    bio:associatedWith bio:{disease_local} ;",
                f'    bio:hasScore "{score}"^^{XSD_DECIMAL} .',
            ]
        )

    return "\n".join(lines) + "\n"


def merge_turtle_documents(chunks: list[str]) -> str:
    """Concatenate Turtle docs sharing the same biomedical prefix."""
    if not chunks:
        return (
            "@prefix bio: <https://ontoharness.dev/biomedical#> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        )
    header = (
        "@prefix bio: <https://ontoharness.dev/biomedical#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n"
    )
    bodies: list[str] = []
    for chunk in chunks:
        stripped = chunk.strip()
        for line in stripped.splitlines():
            if line.startswith("@prefix"):
                continue
            bodies.append(line)
    return header + "\n".join(bodies).strip() + "\n"


def _safe_local(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)
    return cleaned.strip("-") or "item"
