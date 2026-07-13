from fastapi import APIRouter, HTTPException, Query

from app.db import get_session
from app.evidence import parse_evidence_items
from app.models.schemas import (
    DiseaseDetail,
    DiseaseGenesResponse,
    DiseaseSummary,
    ScoredGeneTarget,
)

router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get("", response_model=list[DiseaseSummary])
def search_diseases(q: str = Query("", min_length=0)) -> list[DiseaseSummary]:
    with get_session() as session:
        result = session.run(
            """
            MATCH (d:Disease)
            WHERE $q = '' OR toLower(d.name) CONTAINS toLower($q)
               OR toLower(d.id) CONTAINS toLower($q)
            RETURN d.id AS id, d.name AS name
            ORDER BY d.name
            LIMIT 25
            """,
            q=q,
        )
        return [DiseaseSummary(id=r["id"], name=r["name"]) for r in result]


@router.get("/{disease_id}", response_model=DiseaseDetail)
def get_disease(disease_id: str) -> DiseaseDetail:
    with get_session() as session:
        row = session.run(
            """
            MATCH (d:Disease {id: $id})
            OPTIONAL MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d)
            RETURN d.id AS id, d.name AS name, count(DISTINCT g) AS gene_count
            """,
            id=disease_id,
        ).single()
    if not row:
        raise HTTPException(status_code=404, detail="Disease not found")
    return DiseaseDetail(id=row["id"], name=row["name"], gene_count=row["gene_count"])


@router.get("/{disease_id}/genes", response_model=DiseaseGenesResponse)
def get_disease_genes(
    disease_id: str,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(25, ge=1, le=100),
) -> DiseaseGenesResponse:
    with get_session() as session:
        disease = session.run(
            "MATCH (d:Disease {id: $id}) RETURN d.id AS id, d.name AS name",
            id=disease_id,
        ).single()
        if not disease:
            raise HTTPException(status_code=404, detail="Disease not found")

        rows = session.run(
            """
            MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(d:Disease {id: $id})
            WHERE r.score >= $min_score
            RETURN g.id AS gene_id, g.symbol AS symbol, g.name AS name, r.score AS score,
                   r.source AS source, r.evidence_json AS evidence_json
            ORDER BY r.score DESC
            LIMIT $limit
            """,
            id=disease_id,
            min_score=min_score,
            limit=limit,
        )
        genes = [
            ScoredGeneTarget(
                gene_id=r["gene_id"],
                symbol=r["symbol"],
                name=r["name"],
                score=float(r["score"]),
                source=r.get("source"),
                evidence=parse_evidence_items(r.get("evidence_json")),
            )
            for r in rows
        ]

    return DiseaseGenesResponse(
        disease_id=disease["id"],
        disease_name=disease["name"],
        min_score=min_score,
        genes=genes,
    )
