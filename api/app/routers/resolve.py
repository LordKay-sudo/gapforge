from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.db import get_session
from app.resolve_service import EntityType, resolve

router = APIRouter(tags=["resolve"])


@router.get("/resolve")
def resolve_identifier(
    query: str = Query(..., min_length=1, description="Gene symbol, disease name, or ontology id"),
    entity_type: EntityType = Query(..., description="gene or disease"),
):
    with get_session() as session:
        body = resolve(session, query, entity_type)
    if body.get("error"):
        return JSONResponse(status_code=404, content=body)
    return body
