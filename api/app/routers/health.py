from fastapi import APIRouter

from app.db import check_connectivity
from app import metadata
from app.models.schemas import DataSourceMeta, HealthResponse, MetaResponse, StatsResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    neo4j_ok = check_connectivity()
    return HealthResponse(status="ok" if neo4j_ok else "degraded", neo4j=neo4j_ok)


@router.get("/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    """Service and dataset provenance (no Neo4j required)."""
    return MetaResponse(
        service=metadata.SERVICE_NAME,
        api_version=metadata.API_VERSION,
        data_version=metadata.DATA_VERSION,
        release_date=metadata.RELEASE_DATE.isoformat(),
        sources=[DataSourceMeta(**s) for s in metadata.SOURCES],
        disclaimer=metadata.DISCLAIMER,
        associations_are_correlative=metadata.ASSOCIATIONS_ARE_CORRELATIVE,
        provenance_doc=metadata.PROVENANCE_DOC_PATH,
        web_ui_gene_path="/gene/{gene_id}",
    )


@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    from app.db import get_session

    with get_session() as session:
        row = session.run(
            """
            RETURN
              count { (g:Gene) } AS genes,
              count { (d:Disease) } AS diseases,
              count { (p:Protein) } AS proteins,
              count { ()-[:ASSOCIATED_WITH]->() } AS associations
            """
        ).single()
    return StatsResponse(
        genes=row["genes"],
        diseases=row["diseases"],
        proteins=row["proteins"],
        associations=row["associations"],
    )
