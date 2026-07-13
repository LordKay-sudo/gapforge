import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app import metadata
from app.db import get_session
from app.evidence import parse_evidence_items
from app.models.schemas import SubgraphLink, SubgraphNode, SubgraphResponse

router = APIRouter(prefix="/export", tags=["export"])

GENE_REPORT_COLUMNS = [
    "gene_id",
    "gene_symbol",
    "disease_id",
    "disease_name",
    "score",
    "source",
    "evidence_types",
    "data_version",
    "release_date",
]


@router.get("/subgraph", response_model=SubgraphResponse)
def export_subgraph(gene_id: str = Query(..., description="Center gene Ensembl ID")) -> SubgraphResponse:
    with get_session() as session:
        exists = session.run("MATCH (g:Gene {id: $id}) RETURN g", id=gene_id).single()
        if not exists:
            raise HTTPException(status_code=404, detail="Gene not found")

        nodes_result = session.run(
            """
            MATCH (g:Gene {id: $id})
            OPTIONAL MATCH (g)-[:ASSOCIATED_WITH]->(d:Disease)
            OPTIONAL MATCH (p:Protein)-[:ENCODED_BY]->(g)
            WITH collect(DISTINCT g) + collect(DISTINCT d) + collect(DISTINCT p) AS raw
            UNWIND raw AS n
            WITH DISTINCT n
            RETURN labels(n)[0] AS label, n.id AS id, n.name AS name, n.symbol AS symbol
            """,
            id=gene_id,
        )
        links_result = session.run(
            """
            MATCH (g:Gene {id: $id})
            OPTIONAL MATCH (g)-[r:ASSOCIATED_WITH]->(d:Disease)
            RETURN g.id AS source, d.id AS target, type(r) AS type, r.score AS score
            UNION
            MATCH (g:Gene {id: $id})
            OPTIONAL MATCH (p:Protein)-[r:ENCODED_BY]->(g)
            RETURN p.id AS source, g.id AS target, type(r) AS type, null AS score
            """,
            id=gene_id,
        )

    nodes = [
        SubgraphNode(id=r["id"], label=r["label"], name=r.get("name"), symbol=r.get("symbol"))
        for r in nodes_result
        if r["id"]
    ]
    links = [
        SubgraphLink(source=r["source"], target=r["target"], type=r["type"], score=r["score"])
        for r in links_result
        if r["source"] and r["target"] and r["type"]
    ]
    return SubgraphResponse(gene_id=gene_id, nodes=nodes, links=links)


def _gene_report_rows(gene_id: str) -> tuple[dict, list[dict]]:
    with get_session() as session:
        gene = session.run(
            "MATCH (g:Gene {id: $id}) RETURN g.id AS id, g.symbol AS symbol",
            id=gene_id,
        ).single()
        if not gene:
            raise HTTPException(status_code=404, detail="Gene not found")

        assoc_rows = session.run(
            """
            MATCH (g:Gene {id: $id})-[r:ASSOCIATED_WITH]->(d:Disease)
            RETURN d.id AS disease_id, d.name AS disease_name, r.score AS score,
                   r.source AS source, r.evidence_json AS evidence_json
            ORDER BY r.score DESC
            """,
            id=gene_id,
        )

        rows: list[dict] = []
        for r in assoc_rows:
            evidence = parse_evidence_items(r.get("evidence_json"))
            evidence_types = "|".join(sorted({e.evidence_type for e in evidence}))
            rows.append(
                {
                    "gene_id": gene["id"],
                    "gene_symbol": gene["symbol"],
                    "disease_id": r["disease_id"],
                    "disease_name": r["disease_name"],
                    "score": round(float(r["score"]), 4),
                    "source": r.get("source") or "opentargets",
                    "evidence_types": evidence_types,
                    "data_version": metadata.DATA_VERSION,
                    "release_date": metadata.RELEASE_DATE.isoformat(),
                }
            )

    return {"id": gene["id"], "symbol": gene["symbol"]}, rows


@router.get("/gene-report")
def export_gene_report(
    gene_id: str = Query(..., description="Gene Ensembl ID"),
    format: str = Query("json", pattern="^(json|tsv)$"),
):
    gene, rows = _gene_report_rows(gene_id)

    if format == "tsv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=GENE_REPORT_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
        filename = f"{gene['symbol']}_gene_report.tsv"
        return PlainTextResponse(
            content=buffer.getvalue(),
            media_type="text/tab-separated-values",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return {
        "gene_id": gene["id"],
        "symbol": gene["symbol"],
        "provenance": {
            "data_version": metadata.DATA_VERSION,
            "release_date": metadata.RELEASE_DATE.isoformat(),
            "disclaimer": metadata.DISCLAIMER,
            "provenance_doc": metadata.PROVENANCE_DOC_PATH,
        },
        "columns": GENE_REPORT_COLUMNS,
        "associations": rows,
    }
