# GapForge ecosystem

Product home: https://github.com/LordKay-sudo/gapforge

| Repository | Role |
|------------|------|
| **[gapforge](https://github.com/LordKay-sudo/gapforge)** | Graph + GapForge API/UI + Flurizan case study |
| [bioinsight-graph](https://github.com/LordKay-sudo/bioinsight-graph) | Upstream disease–target graph platform (shared lineage) |
| [kg-rag-demo](https://github.com/LordKay-sudo/kg-rag-demo) | Citation-grounded literature / ClinicalTrials RAG + PeerLens filter |
| [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp) | MCP tools + `research_program_gaps` agent |
| [peerlens](https://github.com/LordKay-sudo/peerlens) | Paper quality signals (retraction / concern gate) |

## Local layout

```text
OSS/
  gapforge/          # clone this first
  bioinsight-graph/  # optional sibling
  kg-rag-demo/
  embabel-mcp/
  peerlens/
```

## Default ports

| Service | Port |
|---------|------|
| GapForge web | 8080 |
| GapForge API | 8000 |
| Neo4j | 7474 / 7687 |
| kg-rag web / API | 8081 / 8001 |
| kg-rag Neo4j | 7475 / 7688 |
| embabel-mcp SSE | 1337 |

## Safety

See [GAPFORGE.md](./GAPFORGE.md) and [HUMAN_IN_THE_LOOP.md](./HUMAN_IN_THE_LOOP.md).
