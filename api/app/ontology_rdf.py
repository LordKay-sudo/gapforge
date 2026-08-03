"""Build biomedical RDF for OntoHarness from GapForge hypothesis context."""
from __future__ import annotations

from xml.sax.saxutils import escape


def _lit(value: str) -> str:
    return f'"{escape(value)}"'


def gap_hypothesis_to_turtle(
    gap_id: str,
    claim: str,
    confidence: float,
    genes: list[dict] | None = None,
    disease: dict | None = None,
) -> str:
    """
    Minimal Turtle aligned with domains/biomedical in OntoHarness.
    genes: [{id, symbol}]
    disease: {id, name}
    """
    lines = [
        "@prefix bio: <https://ontoharness.dev/biomedical#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        f"bio:{_safe_local(gap_id)} a bio:Hypothesis ;",
        f"    rdfs:label {_lit(claim)} .",
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
                f"    bio:associatedWith bio:{disease_local} ;",
                f'    bio:hasScore "{score}"^^<http://www.w3.org/2001/XMLSchema#decimal> .',
            ]
        )

    return "\n".join(lines) + "\n"


def _safe_local(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)
    return cleaned.strip("-") or "item"
