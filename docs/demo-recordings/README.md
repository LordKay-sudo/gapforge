# Recorded demo outputs

Captured from a **live Docker stack** (GapForge + OntoHarness).

**Re-record (stack running on localhost):**

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
