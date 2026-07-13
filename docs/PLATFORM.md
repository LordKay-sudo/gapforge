# Platform — services, ports, and run order

One document to run the whole BioInsight Graph stack (roadmap 4.3).

## Services

| Service | Image / build | Port(s) | Role |
|---------|---------------|---------|------|
| `neo4j` | `neo4j:5.26-community` | `7474` (HTTP browser), `7687` (Bolt) | Graph database holding `Gene`, `Disease`, `Protein` nodes and `ASSOCIATED_WITH` / `ENCODED_BY` edges |
| `seed`  | `Dockerfile.seed` | — (runs once, exits) | Builds the frozen slice + loads it into Neo4j, then completes |
| `api`   | `api/Dockerfile` (FastAPI/uvicorn) | `8000` | REST API at `/api/v1`, OpenAPI at `/docs` |
| `web`   | `web/Dockerfile` (Vite build → nginx) | `8080` → container `80` | React UI |

## Startup order

`docker compose up` resolves this automatically via `depends_on` + healthchecks:

```
neo4j  (healthy)
  └─> seed  (runs to completion)
        └─> api  (healthy)
              └─> web
```

1. **neo4j** starts and reports healthy (`wget` against `:7474`).
2. **seed** waits for neo4j health, runs `build_frozen_slice.py` + `seed_neo4j.py`, then exits `0`.
3. **api** waits for neo4j health **and** seed success, then serves `/api/v1` (health probe on `/api/v1/health`).
4. **web** waits for api health, then serves the UI on `:8080`.

## Quick start

```bash
docker compose up --build        # full stack
# UI:   http://localhost:8080
# API:  http://localhost:8000/docs
# Neo4j Browser: http://localhost:7474
```

If port **8000** is already in use on your machine, copy the override example and remap the API:

```bash
cp docker-compose.override.example.yml docker-compose.override.yml
docker compose up --build   # API on :8001, UI still on :8080
```

## Local (no Docker)

```bash
# 1. Neo4j running locally on bolt://localhost:7687
# 2. Build + seed data
py -3 scripts/build_frozen_slice.py
py -3 scripts/seed_neo4j.py
# 3. API
cd api && uvicorn app.main:app --reload --port 8000
# 4. UI
cd web && npm install && npm run dev      # http://localhost:5173
```

## Environment variables

| Variable | Default | Used by |
|----------|---------|---------|
| `NEO4J_URI` | `bolt://neo4j:7687` (compose) / `bolt://localhost:7687` (local) | api, seed |
| `NEO4J_USER` | `neo4j` | api, seed |
| `NEO4J_PASSWORD` | `changeme` | api, seed |
| `CORS_ORIGINS` | `http://localhost:8080,http://localhost:5173,http://localhost` | api |

## Data refresh

**Frozen slice (default):** `docker compose up --build` — seed runs `build_frozen_slice.py` inside `Dockerfile.seed`.

**Bulk Open Targets slice (local host):**

```bash
py -3 scripts/download_opentargets_bulk.py --release 24.06 --max-genes 500 --with-evidence
py -3 scripts/etl_opentargets.py --input data/raw/opentargets_bulk.json --strict
py -3 scripts/seed_neo4j.py --strict
py -3 scripts/benchmark_api.py --base-url http://localhost:8000 --iterations 200
```

**Bulk via Docker** (mounts host `data/raw/opentargets_bulk.json`):

```bash
docker compose -f docker-compose.yml -f docker-compose.bulk.yml up --build
```

See [PROVENANCE.md](../PROVENANCE.md) for licence (CC0 1.0). The frozen slice remains the default for CI and offline demos.

## Related docs

- [ARCHITECTURE.md](./ARCHITECTURE.md) — component diagram and request flow
- [ONTOLOGY_SCHEMA.md](./ONTOLOGY_SCHEMA.md) — entity/relation/ID model
- [BENCHMARKS.md](./BENCHMARKS.md) — graph size and latency numbers
- [notebooks/one_gene_exploration.ipynb](../notebooks/one_gene_exploration.ipynb) — one-gene tutorial (roadmap 4.4)
