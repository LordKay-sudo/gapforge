from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import close_driver
from app.routers import diseases, discern, export, gaps, genes, health, programs, resolve, reviews

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_driver()


app = FastAPI(
    title="BioInsight Graph API",
    description="Disease–target knowledge graph + GapForge translational gap hunter (Neo4j)",
    version="0.3.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(genes.router, prefix=API_PREFIX)
app.include_router(diseases.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(resolve.router, prefix=API_PREFIX)
app.include_router(programs.router, prefix=API_PREFIX)
app.include_router(gaps.router, prefix=API_PREFIX)
app.include_router(reviews.router, prefix=API_PREFIX)
app.include_router(discern.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"service": "bioinsight-graph", "docs": "/docs", "api": API_PREFIX}
