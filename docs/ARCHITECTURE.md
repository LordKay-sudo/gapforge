# BioInsight Graph — architecture reference

This document supplements the [README](../README.md). The **application code is unchanged** here — only diagrams and URLs for demos. Cross-repo improvement plan: [PORTFOLIO_ROADMAP.md](./PORTFOLIO_ROADMAP.md).

## System context

```mermaid
flowchart TB
  subgraph users [Researchers and agents]
    U[Browser UI]
    C[Cursor / MCP clients]
  end
  subgraph bioinsight [BioInsight Graph]
    WEB[React + Vite :5173 / :8080]
    API[FastAPI :8000]
    N4j[(Neo4j :7474 / :7687)]
  end
  subgraph integrations [Integrations]
    MCP[embabel-mcp :1337]
    RAG[kg-rag-demo :8001]
  end
  U --> WEB
  WEB --> API
  API --> N4j
  C --> MCP
  MCP --> API
  MCP -.-> RAG
```

## Data pipeline (unchanged)

```mermaid
flowchart LR
  OT[Open Targets sample]
  DL[download_sample.py]
  ETL[etl_opentargets.py]
  SEED[seed_neo4j.py]
  N4j[(Neo4j 5)]
  OT --> DL --> ETL --> SEED --> N4j
```

## Entity–relationship model (ERD)

```mermaid
erDiagram
  GENE ||--o{ ASSOCIATED_WITH : has
  DISEASE ||--o{ ASSOCIATED_WITH : has
  PROTEIN ||--|| GENE : ENCODED_BY

  GENE {
    string id PK
    string symbol
    string name
  }
  DISEASE {
    string id PK
    string name
  }
  PROTEIN {
    string id PK
    string name
  }
  ASSOCIATED_WITH {
    float score
    string source
  }
```

## Browser endpoints

| What | URL | Credentials |
|------|-----|-------------|
| Search UI (Docker) | http://localhost:8080 | — |
| Search UI (dev) | http://localhost:5173 | — |
| API Swagger | http://localhost:8000/docs | — |
| Neo4j Browser | http://localhost:7474 | `neo4j` / `changeme` |
| Gene detail example | http://localhost:8080/gene/{gene_id} | — |
| MCP SSE (optional) | http://localhost:1337/sse | — |

Replace `{gene_id}` with an Ensembl id from search (e.g. after searching BRCA1).

## UI screenshots (repository assets)

| Asset | Description |
|-------|-------------|
| [screenshot-search.png](screenshot-search.png) | Tabbed gene/disease search |
| [screenshot-graph.png](screenshot-graph.png) | Force-directed 1-hop subgraph |
| [screenshot-gene-detail.png](screenshot-gene-detail.png) | Full gene page with stats + graph |

See [DEMO.md](DEMO.md) for recording a walkthrough GIF without changing the app.
