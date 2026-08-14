# Recorded demo outputs

Captured from a **live Docker stack** (GapForge + OntoHarness).

**Full stack (GapForge + OntoHarness + Embabel MCP):**

```bash
docker compose -f docker-compose.full.yml up --build   # OPENAI_API_KEY in .env

node scripts/capture_fullstack_demo.mjs
python scripts/record_mcp_demo_outputs.py
cd scripts && npm install && cd ..
node scripts/invoke_mcp_tools.mjs
node scripts/capture_mcp_session_screenshot.mjs
```

**OntoHarness + HITL only:**

```bash
docker compose -f docker-compose.yml -f docker-compose.ontoharness.yml up --build

# UI screenshots first (endpoint must still be needs_review for pass screenshot)
cd web && npx playwright install chromium && cd ..
node scripts/capture_ontoharness_demo.mjs
node scripts/capture_demo_walkthrough.mjs

# Terminal outputs + manifest (approves gap-flurizan-endpoint for export trail)
ONTOHARNESS_BASE_URL=http://localhost:8010 python scripts/record_demo_outputs.py
```

Convert WebM → GIF locally (optional, requires ffmpeg):

```bash
ffmpeg -i demo-walkthrough.webm -vf "fps=8,scale=1280:-1" demo-walkthrough.gif
```

## Files

| File | What it shows |
|------|----------------|
| [00-preflight.txt](./00-preflight.txt) | Stack health checks (`:8000`, `:8010`) |
| [01-validate-demo.txt](./01-validate-demo.txt) | Valid graph passes; `hasTherapeuticTarget` blocked |
| [02-bridge-gap-record.json](./02-bridge-gap-record.json) | Flurizan endpoint gap → Turtle + `conforms: true` |
| [03-fabricated-predicate.json](./03-fabricated-predicate.json) | Raw API response for LLM-hallucinated predicate |
| [04-gapforge-ontology-tests.txt](./04-gapforge-ontology-tests.txt) | GapForge approve gate tests (3 passed) |
| [05-competency-score.json](./05-competency-score.json) | OntoHarness v0.6 — `cq-association-score` SHACL fail (score > 1.0) |
| [06-ontology-validate-endpoint.json](./06-ontology-validate-endpoint.json) | GapForge `/ontology-validate` on `gap-flurizan-endpoint` |
| [07-approve-endpoint.json](./07-approve-endpoint.json) | Approve `gap-flurizan-endpoint` after validation passes |
| [08-export-approved-rdf.ttl](./08-export-approved-rdf.ttl) | Exported Turtle after approve |
| [09-mcp-fullstack-preflight.txt](./09-mcp-fullstack-preflight.txt) | Full stack health — API, OntoHarness, MCP |
| [10-mcp-health.json](./10-mcp-health.json) | Embabel MCP actuator health (`:1337`) |
| [11-program-dossier.json](./11-program-dossier.json) | Flurizan program dossier (MCP `build_program_dossier` REST equivalent) |
| [12-flurizan-gaps.json](./12-flurizan-gaps.json) | Seeded L2 gaps for `prog-flurizan-ad` |
| [screenshot-gapforge-api-docs.png](./screenshot-gapforge-api-docs.png) | GapForge API Swagger (`:8000/docs`) |
| [screenshot-mcp-health.png](./screenshot-mcp-health.png) | MCP health JSON (`:1337/actuator/health`) |
| [screenshot-program-detail.png](./screenshot-program-detail.png) | Flurizan program page in GapForge UI |
| [demo-fullstack-walkthrough.webm](./demo-fullstack-walkthrough.webm) | Full stack recording — API docs → MCP → program → review queue |
| [13-mcp-tool-catalog.json](./13-mcp-tool-catalog.json) | 35 MCP tools listed via SSE |
| [14-mcp-tool-session.md](./14-mcp-tool-session.md) | Live MCP tool calls (health, plan, dossier, ontology validate) |
| [screenshot-mcp-tool-session.png](./screenshot-mcp-tool-session.png) | Rendered MCP tool session summary |
| [mcp-tool-session-capture.html](./mcp-tool-session-capture.html) | Static HTML fallback for MCP session |
| [screenshot-review-ontology-fail.png](./screenshot-review-ontology-fail.png) | HITL — `gap-flurizan-efficacy` vocab failure (`hasTherapeuticTarget`) |
| [screenshot-review-competency-fail.png](./screenshot-review-competency-fail.png) | HITL — `gap-flurizan-cq-demo` competency question failure (v0.6) |
| [screenshot-review-ontology-pass.png](./screenshot-review-ontology-pass.png) | HITL — `gap-flurizan-endpoint` conforms; approve enabled |
| [screenshot-ontoharness-api-v0.6.png](./screenshot-ontoharness-api-v0.6.png) | Live Swagger — validate + `bridge/gap-record` |
| [screenshot-ontoharness-docs.png](./screenshot-ontoharness-docs.png) | Swagger UI (alias capture) |
| [demo-walkthrough.webm](./demo-walkthrough.webm) | Screen recording — Swagger → review queue scroll |
| [review-ui-capture.html](./review-ui-capture.html) | Static fallback when Docker unavailable |
| [manifest.json](./manifest.json) | Recording metadata |

## Highlights (2026-08-13)

**OntoHarness v0.6** — competency question SPARQL gate (`cq-association-score`) blocks graphs with association scores outside [0, 1].

**Fabricated predicate blocked:**

```json
"term": "https://ontoharness.dev/biomedical#hasTherapeuticTarget",
"message": "Undeclared property in policed namespace"
```

Seeded on `gap-flurizan-efficacy` (vocab) and `gap-flurizan-cq-demo` (competency) in the HITL review UI (see screenshots + WebM).

**Approve → RDF export trail:** files `06`–`08` show validate → approve → Turtle export for `gap-flurizan-endpoint`.

## Highlights (2026-08-14)

**Full stack with MCP** — `docker-compose.full.yml` with `OPENAI_API_KEY`. Terminal files `09`–`12` plus `demo-fullstack-walkthrough.webm` show API docs, MCP health, program dossier, and HITL review flow.

**Live MCP tool session (`invoke_mcp_tools.mjs`):** `14-mcp-tool-session.md` records real SSE tool calls — `bioinsight_health`, `plan_gap_investigation`, `build_program_dossier`, `run_gap_ontology_validate`, `list_ontoharness_domains` — against `:1337/sse`.
