from fastapi import APIRouter, HTTPException, Query



from app.db import get_session

from app.evidence import parse_evidence_items
from app.external_links import build_gene_external_links

from app.models.schemas import (

    AssociationEvidenceBundle,

    BatchLookupHit,

    BatchLookupRequest,

    BatchLookupResponse,

    CompareGenesResponse,

    GeneCompareSummary,

    GeneDetail,

    GeneDiseasesResponse,

    GeneEvidenceResponse,

    GeneExternalLinksResponse,

    GeneSummary,

    NeighborEdge,

    NeighborNode,

    NeighborsResponse,

    ScoredDiseaseAssociation,

)



router = APIRouter(prefix="/genes", tags=["genes"])





def _disease_association_from_row(r) -> ScoredDiseaseAssociation:

    return ScoredDiseaseAssociation(

        disease_id=r["disease_id"],

        name=r["name"],

        score=float(r["score"]),

        source=r.get("source"),

        evidence=parse_evidence_items(r.get("evidence_json")),

    )





@router.get("", response_model=list[GeneSummary])

def search_genes(q: str = Query("", min_length=0)) -> list[GeneSummary]:

    with get_session() as session:

        result = session.run(

            """

            MATCH (g:Gene)

            WHERE $q = '' OR toLower(g.symbol) CONTAINS toLower($q)

               OR toLower(coalesce(g.name, '')) CONTAINS toLower($q)

            RETURN g.id AS id, g.symbol AS symbol, g.name AS name

            ORDER BY g.symbol

            LIMIT 25

            """,

            q=q,

        )

        return [GeneSummary(id=r["id"], symbol=r["symbol"], name=r["name"]) for r in result]





@router.get("/compare", response_model=CompareGenesResponse)

def compare_genes(

    symbols: str = Query(..., description="Comma-separated gene symbols, e.g. BRCA1,TP53"),

    top_n: int = Query(5, ge=1, le=25),

) -> CompareGenesResponse:

    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

    if len(symbol_list) < 2:

        raise HTTPException(status_code=400, detail="Provide at least two symbols separated by commas")

    if len(symbol_list) > 5:

        raise HTTPException(status_code=400, detail="At most 5 symbols per comparison")



    summaries: list[GeneCompareSummary] = []

    disease_sets: list[set[str]] = []



    with get_session() as session:

        for symbol in symbol_list:

            gene = session.run(

                """

                MATCH (g:Gene)

                WHERE toLower(g.symbol) = toLower($symbol)

                RETURN g.id AS id, g.symbol AS symbol, g.name AS name

                LIMIT 1

                """,

                symbol=symbol,

            ).single()

            if not gene:

                raise HTTPException(status_code=404, detail=f"Gene not found: {symbol}")



            detail = session.run(

                """

                MATCH (g:Gene {id: $id})

                OPTIONAL MATCH (g)-[:ASSOCIATED_WITH]->(d:Disease)

                RETURN count(DISTINCT d) AS disease_count

                """,

                id=gene["id"],

            ).single()



            disease_rows = session.run(

                """

                MATCH (g:Gene {id: $id})-[r:ASSOCIATED_WITH]->(d:Disease)

                RETURN d.id AS disease_id, d.name AS name, r.score AS score,

                       r.source AS source, r.evidence_json AS evidence_json

                ORDER BY r.score DESC

                LIMIT $top_n

                """,

                id=gene["id"],

                top_n=top_n,

            )

            top_diseases = [_disease_association_from_row(r) for r in disease_rows]

            disease_sets.append({d.name for d in top_diseases})

            summaries.append(

                GeneCompareSummary(

                    gene_id=gene["id"],

                    symbol=gene["symbol"],

                    name=gene["name"],

                    disease_count=detail["disease_count"],

                    top_diseases=top_diseases,

                )

            )



    overlap: set[str] = disease_sets[0]

    for ds in disease_sets[1:]:

        overlap &= ds



    return CompareGenesResponse(

        symbols=symbol_list,

        genes=summaries,

        overlapping_disease_names=sorted(overlap),

    )





@router.get("/{gene_id}/diseases", response_model=GeneDiseasesResponse)

def get_gene_diseases(

    gene_id: str,

    min_score: float = Query(0.0, ge=0.0, le=1.0),

    limit: int = Query(25, ge=1, le=100),

) -> GeneDiseasesResponse:

    with get_session() as session:

        gene = session.run(

            "MATCH (g:Gene {id: $id}) RETURN g.id AS id, g.symbol AS symbol",

            id=gene_id,

        ).single()

        if not gene:

            raise HTTPException(status_code=404, detail="Gene not found")



        rows = session.run(

            """

            MATCH (g:Gene {id: $id})-[r:ASSOCIATED_WITH]->(d:Disease)

            WHERE r.score >= $min_score

            RETURN d.id AS disease_id, d.name AS name, r.score AS score,

                   r.source AS source, r.evidence_json AS evidence_json

            ORDER BY r.score DESC

            LIMIT $limit

            """,

            id=gene_id,

            min_score=min_score,

            limit=limit,

        )

        diseases = [_disease_association_from_row(r) for r in rows]



    return GeneDiseasesResponse(

        gene_id=gene["id"],

        symbol=gene["symbol"],

        min_score=min_score,

        diseases=diseases,

    )





@router.get("/{gene_id}/evidence", response_model=GeneEvidenceResponse)

def get_gene_evidence(

    gene_id: str,

    disease_id: str | None = Query(None, description="Filter to one disease association"),

    limit: int = Query(25, ge=1, le=100),

) -> GeneEvidenceResponse:

    with get_session() as session:

        gene = session.run(

            "MATCH (g:Gene {id: $id}) RETURN g.id AS id, g.symbol AS symbol",

            id=gene_id,

        ).single()

        if not gene:

            raise HTTPException(status_code=404, detail="Gene not found")



        rows = session.run(

            """

            MATCH (g:Gene {id: $id})-[r:ASSOCIATED_WITH]->(d:Disease)

            WHERE $disease_id IS NULL OR d.id = $disease_id

            RETURN d.id AS disease_id, d.name AS disease_name, r.score AS score,

                   r.source AS source, r.evidence_json AS evidence_json

            ORDER BY r.score DESC

            LIMIT $limit

            """,

            id=gene_id,

            disease_id=disease_id,

            limit=limit,

        )

        bundles = [

            AssociationEvidenceBundle(

                disease_id=r["disease_id"],

                disease_name=r["disease_name"],

                score=float(r["score"]),

                source=r.get("source") or "opentargets",

                evidence=parse_evidence_items(r.get("evidence_json")),

            )

            for r in rows

        ]



        if disease_id and not bundles:

            raise HTTPException(

                status_code=404,

                detail=f"No association for gene {gene_id} and disease {disease_id}",

            )



    return GeneEvidenceResponse(

        gene_id=gene["id"],

        symbol=gene["symbol"],

        disease_id=disease_id,

        evidence=bundles,

    )


@router.post("/batch-lookup", response_model=BatchLookupResponse)
def batch_lookup(payload: BatchLookupRequest) -> BatchLookupResponse:
    hits: list[BatchLookupHit] = []
    unresolved: list[str] = []
    seen_queries: set[str] = set()

    with get_session() as session:
        for raw in payload.queries:
            query = raw.strip()
            if not query or query.lower() in seen_queries:
                continue
            seen_queries.add(query.lower())

            row = session.run(
                """
                MATCH (g:Gene)
                WHERE g.id = $q OR toLower(g.symbol) = toLower($q)
                OPTIONAL MATCH (g)-[:ASSOCIATED_WITH]->(d:Disease)
                RETURN g.id AS id, g.symbol AS symbol, g.name AS name,
                       count(DISTINCT d) AS disease_count
                LIMIT 1
                """,
                q=query,
            ).single()

            if row:
                hits.append(
                    BatchLookupHit(
                        query=query,
                        gene_id=row["id"],
                        symbol=row["symbol"],
                        name=row["name"],
                        disease_count=row["disease_count"],
                    )
                )
            else:
                unresolved.append(query)

    return BatchLookupResponse(hits=hits, unresolved=unresolved)


@router.get("/{gene_id}/external-links", response_model=GeneExternalLinksResponse)
def get_gene_external_links(gene_id: str) -> GeneExternalLinksResponse:
    with get_session() as session:
        gene = session.run(
            "MATCH (g:Gene {id: $id}) RETURN g.id AS id, g.symbol AS symbol",
            id=gene_id,
        ).single()
        if not gene:
            raise HTTPException(status_code=404, detail="Gene not found")

        protein_rows = session.run(
            """
            MATCH (p:Protein)-[:ENCODED_BY]->(g:Gene {id: $id})
            RETURN p.id AS id
            ORDER BY p.id
            LIMIT 5
            """,
            id=gene_id,
        )
        uniprot_ids = [r["id"] for r in protein_rows]

    return build_gene_external_links(gene["id"], gene["symbol"], uniprot_ids)


@router.get("/{gene_id}/neighbors", response_model=NeighborsResponse)

def get_neighbors(gene_id: str) -> NeighborsResponse:

    with get_session() as session:

        exists = session.run("MATCH (g:Gene {id: $id}) RETURN g", id=gene_id).single()

        if not exists:

            raise HTTPException(status_code=404, detail="Gene not found")



        nodes_result = session.run(

            """

            MATCH (g:Gene {id: $id})

            OPTIONAL MATCH (g)-[r:ASSOCIATED_WITH]->(d:Disease)

            OPTIONAL MATCH (p:Protein)-[:ENCODED_BY]->(g)

            WITH collect(DISTINCT g) + collect(DISTINCT d) + collect(DISTINCT p) AS raw

            UNWIND raw AS n

            WITH DISTINCT n

            RETURN

              labels(n)[0] AS label,

              n.id AS id,

              n.name AS name,

              n.symbol AS symbol

            """,

            id=gene_id,

        )

        edges_result = session.run(

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

        NeighborNode(id=r["id"], label=r["label"], name=r.get("name"), symbol=r.get("symbol"))

        for r in nodes_result

        if r["id"]

    ]

    edges = [

        NeighborEdge(source=r["source"], target=r["target"], type=r["type"], score=r["score"])

        for r in edges_result

        if r["source"] and r["target"] and r["type"]

    ]

    return NeighborsResponse(gene_id=gene_id, nodes=nodes, edges=edges)





@router.get("/{gene_id}", response_model=GeneDetail)

def get_gene(gene_id: str) -> GeneDetail:

    with get_session() as session:

        row = session.run(

            """

            MATCH (g:Gene {id: $id})

            OPTIONAL MATCH (g)-[:ASSOCIATED_WITH]->(d:Disease)

            OPTIONAL MATCH (p:Protein)-[:ENCODED_BY]->(g)

            RETURN g.id AS id, g.symbol AS symbol, g.name AS name,

                   count(DISTINCT d) AS disease_count,

                   count(DISTINCT p) AS protein_count

            """,

            id=gene_id,

        ).single()

    if not row:

        raise HTTPException(status_code=404, detail="Gene not found")

    return GeneDetail(

        id=row["id"],

        symbol=row["symbol"],

        name=row["name"],

        disease_count=row["disease_count"],

        protein_count=row["protein_count"],

    )


