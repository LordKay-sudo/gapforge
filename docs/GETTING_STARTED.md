# Getting started — public data → Neo4j → API

Tutorial path (roadmap 5.2): clone to running API in ~15 minutes.

## 1. Clone and configure

```bash
git clone https://github.com/LordKay-sudo/bioinsight-graph.git
cd bioinsight-graph
cp .env.example .env
```

## 2. Full stack (recommended)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8080 |
| API docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

The `seed` job loads the **Open Targets 24.06 frozen slice** (CC0 public data) into Neo4j. See [PROVENANCE.md](../PROVENANCE.md).

## 3. Verify the graph

```bash
curl http://localhost:8000/api/v1/stats
curl "http://localhost:8000/api/v1/genes?q=BRCA1"
curl http://localhost:8000/api/v1/genes/ENSG00000012048/evidence
```

In the UI: search **BRCA1** → open gene detail → switch to **Compare** or search a disease.

## 4. Local dev (no Docker UI)

```bash
docker compose up -d neo4j
py -3 scripts/build_frozen_slice.py
py -3 scripts/seed_neo4j.py
cd api && uvicorn app.main:app --reload --port 8000
cd web && npm install && npm run dev
```

## 5. Notebook walkthrough (roadmap 4.4)

With the stack running:

```bash
cd api && pip install -r requirements.txt -r ../notebooks/requirements.txt
jupyter notebook ../notebooks/one_gene_exploration.ipynb
```

See [notebooks/README.md](../notebooks/README.md).

## 6. Agent / MCP layer (optional)

Point [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp) at `http://localhost:8000/api/v1`. Use MCP prompt **`public-data-to-mcp-tutorial`** for a guided Cursor setup.

## Strict production ingest

For real bulk Open Targets data with ontology validation:

```bash
py -3 scripts/download_opentargets_bulk.py --release 24.06 --max-genes 500
py -3 scripts/etl_opentargets.py --input data/raw/opentargets_bulk.json --strict
py -3 scripts/seed_neo4j.py --strict
```

See [ONTOLOGY_SCHEMA.md](./ONTOLOGY_SCHEMA.md) and [BENCHMARKS.md](./BENCHMARKS.md).
